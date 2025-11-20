from django.contrib import admin
from django.utils.html import format_html

from .models import Accommodation, Booker, Booking


@admin.register(Booker)
class BookerAdmin(admin.ModelAdmin):
    """Admin interface for Booker model"""

    list_display = ["name", "email", "phone", "group_size", "created_at"]
    list_filter = ["group_size", "created_at"]
    search_fields = ["name", "email", "phone"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = (
        ("Contact Information", {"fields": ("name", "email", "phone")}),
        ("Group Details", {"fields": ("group_size",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    """Admin interface for Accommodation model"""

    list_display = [
        "name",
        "capacity",
        "price_per_night",
        "is_active",
        "booking_count",
        "created_at",
    ]
    list_filter = ["is_active", "capacity", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["name"]

    fieldsets = (
        ("Basic Information", {"fields": ("name", "description")}),
        ("Capacity & Pricing", {"fields": ("capacity", "price_per_night")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def booking_count(self, obj):
        """Display number of active bookings"""
        count = obj.bookings.filter(status__in=["pending", "confirmed"]).count()
        return count

    booking_count.short_description = "Active Bookings"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model"""

    list_display = [
        "id",
        "accommodation",
        "booker_name",
        "start_date",
        "end_date",
        "duration",
        "number_of_guests",
        "status_badge",
        "created_at",
    ]
    list_filter = ["status", "start_date", "end_date", "created_at"]
    search_fields = ["accommodation__name", "booker__name", "booker__email"]
    readonly_fields = ["created_at", "updated_at", "version", "duration_display"]
    date_hierarchy = "start_date"
    ordering = ["-created_at"]
    list_select_related = ["accommodation", "booker"]

    fieldsets = (
        (
            "Booking Details",
            {
                "fields": (
                    "accommodation",
                    "booker",
                    "start_date",
                    "end_date",
                    "duration_display",
                    "number_of_guests",
                )
            },
        ),
        ("Status", {"fields": ("status",)}),
        (
            "System Fields",
            {
                "fields": ("version", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["confirm_bookings", "cancel_bookings"]

    def booker_name(self, obj):
        """Display booker name"""
        return obj.booker.name

    booker_name.short_description = "Booker"
    booker_name.admin_order_field = "booker__name"

    def duration(self, obj):
        """Display booking duration in nights"""
        return f"{obj.duration_nights()} nights"

    duration.short_description = "Duration"

    def duration_display(self, obj):
        """Display duration for detail view"""
        if obj.id:
            return f"{obj.duration_nights()} nights"
        return "N/A (save to calculate)"

    duration_display.short_description = "Duration"

    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            "pending": "#FFA500",  # Orange
            "confirmed": "#28A745",  # Green
            "cancelled": "#DC3545",  # Red
        }
        color = colors.get(obj.status, "#6C757D")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def confirm_bookings(self, request, queryset):
        """Admin action to confirm selected bookings"""
        confirmed = 0
        for booking in queryset:
            if booking.can_confirm():
                booking.confirm()
                booking.save()
                confirmed += 1

        self.message_user(
            request,
            f"Successfully confirmed {confirmed} booking(s).",
        )

    confirm_bookings.short_description = "Confirm selected bookings"

    def cancel_bookings(self, request, queryset):
        """Admin action to cancel selected bookings"""
        cancelled = 0
        for booking in queryset:
            if booking.can_cancel():
                booking.cancel()
                booking.save()
                cancelled += 1

        self.message_user(
            request,
            f"Successfully cancelled {cancelled} booking(s).",
        )

    cancel_bookings.short_description = "Cancel selected bookings"
