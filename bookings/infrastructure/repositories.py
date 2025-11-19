from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import Booker, Accommodation


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


class AccommodationRepository(ABC):
    """Abstract repository interface for Accommodation entities"""

    @abstractmethod
    def get_by_id(self, accommodation_id: int) -> Optional[Accommodation]:
        pass

    @abstractmethod
    def save(self, accommodation: Accommodation) -> Accommodation:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Accommodation]:
        pass

    @abstractmethod
    def get_active(self) -> List[Accommodation]:
        pass


class DjangoAccommodationRepository(AccommodationRepository):
    """Django ORM implementation of AccommodationRepository"""

    def get_by_id(self, accommodation_id: int) -> Optional[Accommodation]:
        try:
            return Accommodation.objects.get(id=accommodation_id, is_active=True)
        except Accommodation.DoesNotExist:
            return None

    def save(self, accommodation: Accommodation) -> Accommodation:
        accommodation.save()
        return accommodation

    def find_by_name(self, name: str) -> Optional[Accommodation]:
        try:
            return Accommodation.objects.get(name=name, is_active=True)
        except Accommodation.DoesNotExist:
            return None

    def get_active(self) -> List[Accommodation]:
        return list(Accommodation.objects.filter(is_active=True))