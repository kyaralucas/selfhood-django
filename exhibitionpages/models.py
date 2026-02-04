from django.core.validators import MaxLengthValidator
from django.db import models

# Create your models here.
class TimeSlot(models.Model):
    time = models.CharField(max_length=5, unique=True) # ex. 19:00
    capacity  = models.PositiveSmallIntegerField(default=15)
    reserved = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"{self.time}  ({self.reserved}/{self.capacity})"
    

    @property 
    def is_full(self) -> bool:
        return self.reserved >= self.capacity 
    

class Registration(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    guests = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional prompt during registration
    prompt_question = models.TextField(blank=True, default="")
    prompt_answer = models.TextField(blank=True, default="", validators=[MaxLengthValidator(1000)],)

    # Chosen slot
    slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name="registrations")


    def __str__(self):
        return f"{self.name} < {self.email}> (+{self.guests}) [{self.slot.time}]"
    
