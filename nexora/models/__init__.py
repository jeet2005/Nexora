"""Model registry, task detection, and training."""

from nexora.models.registry import get_model, get_models_for_task
from nexora.models.task_detector import detect_task_type
from nexora.models.trainer import train_models

__all__ = ["detect_task_type", "get_model", "get_models_for_task", "train_models"]
