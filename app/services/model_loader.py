# services/model_loader.py

from typing import Dict
import torch
import torch.nn as nn
from torchvision import models
from core.config import settings
import numpy as np
from data.class_labels import regression_labels


classification_models = {}
regression_models = {}


def load_models():
    global classification_models, regression_models
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load regression models
    regression_values = list(
        set(value for values in regression_labels.values() for value in values)
    )
    for regression_value in regression_values:
        regression_checkpoint_path = f"{settings.checkpoint_dir}/regression/initialResNet/save_model/{regression_value}/state_dict.bin"
        try:
            regression_model = models.resnet50()
            num_ftrs = regression_model.fc.in_features
            regression_model.fc = nn.Linear(num_ftrs, 1)
            checkpoint = torch.load(
                regression_checkpoint_path, map_location=device, weights_only=True
            )
            regression_model.load_state_dict(checkpoint["model_state"])
            regression_model.to(device)
            regression_model.eval()
            regression_models[regression_value] = regression_model
            print(f"Loaded regression model: {regression_value}")
        except FileNotFoundError:
            print(f"No regression model found: {regression_value}")


def get_classification_model(area_name: str):
    return classification_models.get(area_name)


def get_regression_models(area_name: str) -> Dict[str, nn.Module]:
    result_dict = {}
    regression_values_for_area = regression_labels.get(area_name, [])
    for regression_value in regression_values_for_area:
        regression_model = regression_models.get(regression_value)
        if regression_model is not None:
            result_dict[regression_value] = regression_model

    return result_dict


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
