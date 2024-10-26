# services/model_loader.py

import torch
import torch.nn as nn
from torchvision import models
from core.config import settings
import numpy as np


classification_models = {}
regression_models = {}


def load_models():
    global classification_models, regression_models
    area_names = {
        "0": "full_face",
        "1": "forehead",
        "2": "glabellus",
        "3": "l_perocular",
        "4": "r_perocular",
        "5": "l_cheek",
        "6": "r_cheek",
        "7": "lip",
        "8": "chin",
    }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    for area_num, area_name in area_names.items():
        # Load classification model
        if area_num in ["4", "6"]:
            area_num = str(int(area_num) - 1)
        num_classes = get_num_classes(int(area_num), mode="class")
        if num_classes > 0:
            classification_checkpoint_path = (
                f"{settings.checkpoint_dir}/class/100%/1,2,3/{area_num}/state_dict.bin"
            )
            try:
                classification_model = models.resnet50()
                num_ftrs = classification_model.fc.in_features
                classification_model.fc = nn.Linear(num_ftrs, num_classes)
                checkpoint = torch.load(
                    classification_checkpoint_path,
                    map_location=device,
                    weights_only=True,
                )
                classification_model.load_state_dict(checkpoint["model_state"])
                classification_model.to(device)
                classification_model.eval()
                classification_models[area_name] = classification_model
                print(f"Loaded classification model for area: {area_name}")
            except FileNotFoundError:
                print(f"No classification model found for area: {area_name}")

        # Load regression model
        num_outputs = get_num_classes(int(area_num), mode="regression")
        if num_outputs > 0:
            regression_checkpoint_path = f"{settings.checkpoint_dir}/regression/100%/1,2,3/{area_num}/state_dict.bin"
            try:
                regression_model = models.resnet50()
                num_ftrs = regression_model.fc.in_features
                regression_model.fc = nn.Linear(num_ftrs, num_outputs)
                checkpoint = torch.load(
                    regression_checkpoint_path, map_location=device, weights_only=True
                )
                regression_model.load_state_dict(checkpoint["model_state"])
                regression_model.to(device)
                regression_model.eval()
                regression_models[area_name] = regression_model
                print(f"Loaded regression model for area: {area_name}")
            except FileNotFoundError:
                print(f"No regression model found for area: {area_name}")


def get_classification_model(area_name: str):
    return classification_models.get(area_name)


def get_regression_model(area_name: str):
    return regression_models.get(area_name)


def get_num_classes(area_num, mode="class"):
    if mode == "class":
        model_num_class = [np.nan, 15, 7, 7, 0, 12, 0, 5, 7]
    else:
        model_num_class = [1, 2, np.nan, 1, 0, 3, 0, np.nan, 2]
    num = model_num_class[area_num]
    if np.isnan(num) or num == 0:
        return 0
    else:
        return int(num)
