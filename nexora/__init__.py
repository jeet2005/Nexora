"""Public package API for Nexora v0.1.0."""


from nexora.core import Nexora
from nexora.report import NexoraReport
# Alias for backward compatibility
NexoraPrediction = Nexora

__all__ = ["DatasetProfile", "ModelResult", "Nexora", "NexoraReport", "NexoraPrediction"]

__version__ = "0.1.0"
