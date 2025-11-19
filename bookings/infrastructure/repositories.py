from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import Booker


class BookerRepository(ABC):
    """Abstract repository interface for Booker entities"""

    @abstractmethod
    def get_by_id(self, booker_id: int) -> Optional[Booker]:
        pass

    @abstractmethod
    def save(self, booker: Booker) -> Booker:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Booker]:
        pass

    @abstractmethod
    def get_all(self) -> List[Booker]:
        pass


class DjangoBookerRepository(BookerRepository):
    """Django ORM implementation of BookerRepository"""

    def get_by_id(self, booker_id: int) -> Optional[Booker]:
        try:
            return Booker.objects.get(id=booker_id)
        except Booker.DoesNotExist:
            return None

    def save(self, booker: Booker) -> Booker:
        booker.save()
        return booker

    def find_by_email(self, email: str) -> Optional[Booker]:
        try:
            return Booker.objects.get(email=email)
        except Booker.DoesNotExist:
            return None

    def get_all(self) -> List[Booker]:
        return list(Booker.objects.all())