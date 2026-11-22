from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
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
        limit: int = 5,
        orientation: Optional[str] = None
    ) -> List[FootageClip]:
        """
        Search provider for video clips matching the query.
        """
        pass

    async def check_active_status(self) -> Tuple[bool, str]:
        """
        Lightweight status check. Returns (is_active, status_message).
        """
        if not self.is_available:
            return False, "No key configured"
        return True, "Active"
