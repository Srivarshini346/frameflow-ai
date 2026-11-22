from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.api_schemas import FootageClip

class FootageProviderBase(ABC):
    """
    Abstract interface for video footage providers.
    All integrations (Pexels, Pixabay, Mock) inherit from this adapter.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    async def search_footage(
        self,
        query: str,
        min_duration: float = 3.0,
        limit: int = 5
    ) -> List[FootageClip]:
        """
        Search provider for video clips matching the query.
        """
        pass
