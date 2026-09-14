"""
ModelRegistry: load active model/preprocessor/metadata and expose an
immutable model version. Real implementation lands in Phase 3 (initial
load) and is hardened in Phase 10 (versioning/reproducibility).

Non-negotiable: this module must never train a model. It only loads a
pre-trained, already-approved artifact.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ModelBundle:
    model: Any
    preprocessor: Any
    version: str
    metadata: dict


class ModelRegistry(ABC):
    @abstractmethod
    def load_active(self) -> ModelBundle:
        raise NotImplementedError
