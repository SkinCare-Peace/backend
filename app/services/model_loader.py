# services/model_loader.py

from pprint import pprint
from typing import Dict
import torch
import torch.nn as nn
from torchvision import models
from core.config import settings
import numpy as np
from data.class_labels import regression_labels, class_labels


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

    # Load classification models
    class_values = list(
        set(value for values in class_labels.values() for value in values)
    )
    for class_value in class_values:
        classification_checkpoint_path = f"{settings.checkpoint_dir}/class/initialResNet/save_model/{class_value}/state_dict.bin"
        try:
            classification_model = models.resnet50()
            num_ftrs = classification_model.fc.in_features
            checkpoint = torch.load(
                classification_checkpoint_path, map_location=device, weights_only=True
            )
            if "model_state" in checkpoint:
                output_size = checkpoint["model_state"]["fc.weight"].size(0)
            else:
                raise ValueError("Invalid checkpoint file")

            classification_model.fc = nn.Linear(num_ftrs, output_size)
            classification_model.load_state_dict(checkpoint["model_state"])
            classification_model.to(device)
            classification_model.eval()
            classification_models[class_value] = classification_model
            print(f"Loaded classification model: {class_value}")
        except FileNotFoundError:
            print(f"No classification model found: {class_value}")


def get_classification_model(area_name: str):
    result_dict = {}
    classification_values_for_area = class_labels.get(area_name, [])
    for classification_value in classification_values_for_area:
        classification_model = classification_models.get(classification_value)
        if classification_model is not None:
            result_dict[classification_value] = classification_model
    return result_dict


def get_regression_models(area_name: str) -> Dict[str, nn.Module]:
    result_dict = {}
    regression_values_for_area = regression_labels.get(area_name, [])
    for regression_value in regression_values_for_area:
        regression_model = regression_models.get(regression_value)
        if regression_model is not None:
            result_dict[regression_value] = regression_model

    return result_dict
