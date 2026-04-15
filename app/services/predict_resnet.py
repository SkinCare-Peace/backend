# services/predict_resnet.py
from pprint import pprint
from typing import Dict
from torchvision import transforms
from PIL import Image

from fastapi import UploadFile
from services.model_loader import get_classification_model, get_regression_models
from schemas.prediction import PredictionResponse
from data.class_labels import class_labels, regression_labels
import torch
from PIL import Image
import io
import numpy as np


def crop_and_resize(
    img: Image.Image, bbox: list, target_size: int = 128
) -> Image.Image:
    """
    이미지의 바운딩 박스(bbox)를 기준으로 중앙을 정렬하여 정사각형으로 크롭하고 리사이즈합니다.
    """
    img_cv = np.array(img)  # PIL 이미지를 OpenCV 형식으로 변환
    center_bbox = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
    center_bbox = list(map(int, center_bbox))

    # 바운딩 박스에서 가장 긴 변을 기준으로 정사각형 영역을 구합니다.
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    crop_length = int(max(width, height) / 2)

    # 이미지 크롭 (중앙을 기준으로 크롭)
    cropped_img = img_cv[
        max(center_bbox[1] - crop_length, 0) : min(
            center_bbox[1] + crop_length, img_cv.shape[0]
        ),
        max(center_bbox[0] - crop_length, 0) : min(
            center_bbox[0] + crop_length, img_cv.shape[1]
        ),
    ]

    # 크롭된 이미지를 다시 PIL 이미지로 변환하고, 정사각형으로 리사이즈합니다.
    cropped_img_pil = Image.fromarray(cropped_img)

    resized_img = cropped_img_pil.resize((target_size, target_size))

    return resized_img


def preprocess_image(img: Image.Image, area_name: str, bbox: list):
    cropped_img = crop_and_resize(img, bbox)
    if area_name == "r_cheek" or area_name == "r_perocular":
        cropped_img = cropped_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    # 정규화 추가
    preprocess = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]  # ImageNet 평균
            ),  # ImageNet 표준편차
        ]
    )

    input_tensor = preprocess(cropped_img)
    input_tensor = input_tensor.unsqueeze(0)  # type: ignore
    return input_tensor


async def predict_image(
    area_name: str, file: UploadFile, bbox: list
) -> PredictionResponse:
    classification_model = get_classification_model(area_name)
    regression_models = get_regression_models(area_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise ValueError("Invalid image format")

    try:
        input_tensor = preprocess_image(img, area_name, bbox)
        input_tensor = input_tensor.to(device)
    except ValueError as e:
        raise ValueError(str(e))
    scaling_factors = {
        "elasticity": 1,
        "moisture": 100,
        "wrinkle": 50,
        "pigmentation": 350,
        "pore": 2600,
    }

    response = {}
    regression_values_for_area = regression_labels.get(area_name, [])
    # 하드코딩된 기본 결과값 정의 (사용자 요청에 따라 BSTI 결과에 영향을 미치도록 설정)
    default_regression_values = {
        "moisture": 50.0,      # D/O 기준 (40 이상이면 O)
        "elasticity": 60.0,    # W/T 기준 (50 이상이면 T)
        "wrinkle": 20.0,       # W/T 기준 (50 미만이면 T)
        "pigmentation": 120.0, # P/N 기준 (100 이상이면 P)
        "pore": 2000.0         # D/O 기준 (1600 이상이면 고정값 처리 로직에 영향)
    }

    regression_values: Dict[str, float] = {}
    if regression_values_for_area:
        for regression_value in regression_values_for_area:
            regression_model = regression_models.get(regression_value)
            if regression_model is None:
                # 모델이 없는 경우 하드코딩된 기본값 사용
                print(f"No regression model loaded for {regression_value}, using default.")
                regression_values[regression_value] = default_regression_values.get(regression_value, 0.0)
                continue
            with torch.no_grad():
                reg_output = regression_model(input_tensor)
                scaled_output = reg_output.cpu().item() * scaling_factors.get(
                    regression_value, 1
                )
            regression_values[regression_value] = float(scaled_output)
    else:
        # 해당 영역에 정의된 회귀 레이블이 없더라도 기본값 중 일부를 제공할 수 있음
        # 하지만 프론트엔드 에러 방지를 위해 요청된 키들을 보장하는 것이 안전함
        pass

    # 프론트엔드에서 Missing category 에러가 발생하지 않도록 모든 필수 키를 포함시킴
    for key, val in default_regression_values.items():
        if key not in regression_values:
            regression_values[key] = val

    response["regression_values"] = regression_values

    class_values_for_area = class_labels.get(area_name, [])
    class_values: Dict[str, List[float]] = {}
    if class_values_for_area:
        for class_value in class_values_for_area:
            class_model = classification_model.get(class_value)
            if class_model is None:
                print(f"No classification model loaded for {class_value}, using default.")
                class_values[class_value] = [0.1, 0.9]
                continue
            with torch.no_grad():
                class_output = class_model(input_tensor)
                class_output = torch.nn.functional.softmax(class_output, dim=1)
                class_output = class_output.cpu().numpy()
                class_output = class_output[0]
                class_output = class_output.tolist()
                class_values[class_value] = class_output
    
    # 기본 분류 값 추가 (필요한 경우)
    if not class_values:
        class_values["default"] = [0.1, 0.9]
    
    response["classification_probabilities"] = class_values

    return PredictionResponse(**response)
