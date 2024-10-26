from torchvision import transforms
from PIL import Image

from fastapi import UploadFile
from services.model_loader import get_classification_model, get_regression_model
from schemas.prediction import PredictionResponse
from data.class_labels import class_labels, regression_labels
import torch
from PIL import Image
import io
import numpy as np

def crop_and_resize(img: Image.Image, bbox: list, target_size: int = 128) -> Image.Image:
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
        max(center_bbox[1] - crop_length, 0) : min(center_bbox[1] + crop_length, img_cv.shape[0]),
        max(center_bbox[0] - crop_length, 0) : min(center_bbox[0] + crop_length, img_cv.shape[1])
    ]

    # 크롭된 이미지를 다시 PIL 이미지로 변환하고, 정사각형으로 리사이즈합니다.
    cropped_img_pil = Image.fromarray(cropped_img)
    resized_img = cropped_img_pil.resize((target_size, target_size))
    
    return resized_img

def preprocess_image(img: Image.Image, area_name: str, bbox:list):
    cropped_img = crop_and_resize(img, bbox)
    if area_name == "r_cheek" or area_name == "r_perocular":
        cropped_img = cropped_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    input_tensor = transforms.ToTensor()(cropped_img)
    input_tensor = input_tensor.unsqueeze(0)

    return input_tensor

async def predict_image(area_name: str, file: UploadFile, bbox:list) -> PredictionResponse:
    classification_model = get_classification_model(area_name)
    regression_model = get_regression_model(area_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception:
        raise ValueError("Invalid image format")

    try:
        input_tensor = preprocess_image(img, area_name, bbox)
        input_tensor = input_tensor.to(device)
    except ValueError as e:
        raise ValueError(str(e))

    response = {}

    if classification_model is not None:
        with torch.no_grad():
            class_output = classification_model(input_tensor)
            print("Class Output (Logits):", class_output.cpu().numpy())
        probabilities = torch.nn.functional.softmax(class_output, dim=1)
        _, predicted_class = torch.max(class_output, dim=1)
        labels = class_labels.get(area_name, [])
        if predicted_class.item() < len(labels):
            predicted_label = labels[predicted_class.item()]
        else:
            predicted_label = "Unknown"
        prob_dict = {}
        for idx, prob in enumerate(probabilities.cpu().numpy()[0]):
            if idx < len(labels):
                prob_dict[labels[idx]] = float(prob)
            else:
                prob_dict[f"Class {idx}"] = float(prob)
        response['predicted_class'] = int(predicted_class.item())
        response['predicted_label'] = predicted_label
        response['classification_probabilities'] = prob_dict

    if regression_model is not None:
        with torch.no_grad():
            reg_output = regression_model(input_tensor)
            print("Regression Output:", reg_output.cpu().numpy())
        regression_labels_area = regression_labels.get(area_name, [])
        regression_values = {}
        if len(reg_output[0]) == len(regression_labels_area):
            for idx, label_name in enumerate(regression_labels_area):
                regression_values[label_name] = float(reg_output[0][idx].cpu().numpy())
        else:
            raise ValueError("Mismatch between number of regression outputs and regression labels")
        response['regression_values'] = regression_values

    if not response:
        raise ValueError("No available models for the given area")

    return PredictionResponse(**response)