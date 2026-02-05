from django.contrib import admin
from .models import Registration, TimeSlot

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("time", "reserved_count", "capacity")

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "slot", "guests", "created_at")
    search_fields = ("name", "email")
