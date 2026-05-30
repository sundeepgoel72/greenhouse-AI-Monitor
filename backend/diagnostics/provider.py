from abc import ABC, abstractmethod
from typing import Any

class DiagnosisProvider(ABC):

    @abstractmethod
    async def diagnose(self, image_path: str, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
