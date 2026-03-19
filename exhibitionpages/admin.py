from django.contrib import admin
from .models import Registration, TimeSlot, SimpleRegistration

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("time", "reserved_count", "capacity")

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "slot", "guests", "created_at")
    search_fields = ("name", "email")

@admin.register(SimpleRegistration)
class SimpleRegistrationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "guests", "created_at", "prompt_answer")
    search_fields = ("name", "email")
