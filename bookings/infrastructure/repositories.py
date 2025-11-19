from abc import ABC, abstractmethod

from ..models import Accommodation, Booker, Booking


class BookerRepository(ABC):
    """Abstract repository interface for Booker entities"""

    @abstractmethod
    def get_by_id(self, booker_id: int) -> Booker | None:
        pass

    @abstractmethod
    def save(self, booker: Booker) -> Booker:
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Booker | None:
        pass

    @abstractmethod
    def get_all(self) -> list[Booker]:
        pass


class DjangoBookerRepository(BookerRepository):
    """Django ORM implementation of BookerRepository"""

    def get_by_id(self, booker_id: int) -> Booker | None:
        try:
            return Booker.objects.get(id=booker_id)
        except Booker.DoesNotExist:
            return None

    def save(self, booker: Booker) -> Booker:
        booker.save()
        return booker

    def find_by_email(self, email: str) -> Booker | None:
        try:
            return Booker.objects.get(email=email)
        except Booker.DoesNotExist:
            return None

    def get_all(self) -> list[Booker]:
        return list(Booker.objects.all())


class AccommodationRepository(ABC):
    """Abstract repository interface for Accommodation entities"""

    @abstractmethod
    def get_by_id(self, accommodation_id: int) -> Accommodation | None:
        pass

    @abstractmethod
    def save(self, accommodation: Accommodation) -> Accommodation:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Accommodation | None:
        pass

    @abstractmethod
    def get_active(self) -> list[Accommodation]:
        pass


class DjangoAccommodationRepository(AccommodationRepository):
    """Django ORM implementation of AccommodationRepository"""

    def get_by_id(self, accommodation_id: int) -> Accommodation | None:
        try:
            return Accommodation.objects.get(id=accommodation_id, is_active=True)
        except Accommodation.DoesNotExist:
            return None

    def save(self, accommodation: Accommodation) -> Accommodation:
        accommodation.save()
        return accommodation

    def find_by_name(self, name: str) -> Accommodation | None:
        try:
            return Accommodation.objects.get(name=name, is_active=True)
        except Accommodation.DoesNotExist:
            return None

    def get_active(self) -> list[Accommodation]:
        return list(Accommodation.objects.filter(is_active=True))


class BookingRepository(ABC):
    """Abstract repository interface for Booking entities"""

    @abstractmethod
    def get_by_id(self, booking_id: int) -> Booking | None:
        pass

    @abstractmethod
    def save(self, booking: Booking) -> Booking:
        pass

    @abstractmethod
    def find_by_accommodation_and_dates(
        self, accommodation: Accommodation, start_date, end_date
    ) -> list[Booking]:
        pass

    @abstractmethod
    def get_active_bookings_for_accommodation(self, accommodation: Accommodation) -> list[Booking]:
        pass


class DjangoBookingRepository(BookingRepository):
    """Django ORM implementation of BookingRepository"""

    def get_by_id(self, booking_id: int) -> Booking | None:
        try:
            return Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            return None

    def save(self, booking: Booking) -> Booking:
        booking.save()
        return booking

    def find_by_accommodation_and_dates(
        self, accommodation: Accommodation, start_date, end_date
    ) -> list[Booking]:
        return list(
            Booking.objects.filter(
                accommodation=accommodation,
                start_date__lt=end_date,
                end_date__gt=start_date,
                status__in=["pending", "confirmed"],
            )
        )

    def get_active_bookings_for_accommodation(self, accommodation: Accommodation) -> list[Booking]:
        return list(
            Booking.objects.filter(accommodation=accommodation, status__in=["pending", "confirmed"])
        )
