"""Public package API for Nexora v0.1.1."""

from nexora.core import Nexora
from nexora.report import NexoraReport
from nexora.types import (
    DatasetIntelligence,
    DatasetProfile,
    ModelResult,
    PredictionReceipt,
    TrainingSettings,
)

# Alias for backward compatibility
NexoraPrediction = Nexora

__all__ = [
    "DatasetIntelligence",
    "DatasetProfile",
    "ModelResult",
    "Nexora",
    "NexoraPrediction",
    "NexoraReport",
    "PredictionReceipt",
    "TrainingSettings",
]

__version__ = "0.1.2"
