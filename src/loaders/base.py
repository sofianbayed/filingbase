from abc import ABC, abstractmethod
from src.models.documents import Document

class BaseDocumentLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    async def load(self) -> Document:
        pass

    @staticmethod
    def _is_url(path: str) -> bool:
        """Check if the given path is a URL."""
        return path.startswith("https://")