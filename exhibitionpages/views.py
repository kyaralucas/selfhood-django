import random
from django.shortcuts import render, redirect
from django.db import transaction
from .forms import RegistrationForm
from .models import Registration, TimeSlot
from .questions import QUESTIONS

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

import time 

# For sending emails
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import transaction

# Logging
import logging
logger = logging.getLogger(__name__)

# Create your views here.
def home(request):
    return render(request, "exhibitionpages/home.html")

def rest(request):
    # Random prompts (only those with non-empty answers)
    prompts = (
        Registration.objects
        .exclude(prompt_answer="")
        .exclude(prompt_answer__isnull=True)
        .values("prompt_question", "prompt_answer")
        .order_by("?")[:50]
    )

    # For small datasets, order_by("?") is simplest
    sample_prompts = list(prompts)

    return render(
        request,
        "exhibitionpages/rest.html",
        {"qas": sample_prompts},
    )


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        asked_question = request.POST.get("asked_question", "").strip()

        if form.is_valid():
            with transaction.atomic():
                chosen_slot = form.cleaned_data["slot"]
                guest_count = int(form.cleaned_data.get("guests") or 1)

                # Lock slot row to prevent race conditions
                slot = TimeSlot.objects.select_for_update().get(pk=chosen_slot.pk)

                # Compute current reserved from registrations (sum of guests)
                current_reserved = (
                    slot.registrations.aggregate(total=Coalesce(Sum("guests"), 0))["total"]
                )

                if current_reserved + guest_count > slot.capacity:
                    form.add_error("slot", "That time slot doesn't have enough space. Please choose another one.")
                else:
                    obj = form.save(commit=False)
                    obj.guests = guest_count
                    obj.prompt_question = asked_question
                    obj.slot = slot
                    obj.save()

                    def send_confirmation_email(registration_id: int):
                        reg = (
                            Registration.objects
                            .select_related("slot")
                            .get(pk=registration_id)
                        )

                        subject = "Your SELFHOOD timeslot is confirmed"
                        message = render_to_string(
                            "exhibitionpages/emails/registration_confirmation.txt",
                            {
                                "name": getattr(reg, "name", "there"),
                                "time": reg.slot.time,  # adjust formatting as needed
                            },
                        )

                        send_mail(
                            subject=subject,
                            message=message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[reg.email],
                            fail_silently=False,
                        )

                    try:
                        transaction.on_commit(lambda: send_confirmation_email(obj.pk))
                        # time.sleep(3)
                        logger.exception("Confirmation email SENT for registration %s", obj.pk)
                    except Exception:
                        logger.exception("Confirmation email FAILED for registration %s", obj.pk)
                    

                    request.session["last_registration_id"] = obj.pk
                    return redirect("register_thanks")
    else:
        form = RegistrationForm()
        asked_question = random.choice(QUESTIONS)

    slots = TimeSlot.objects.order_by("time")

    return render(
        request,
        "exhibitionpages/register.html",
        {"form": form, "asked_question": asked_question, "slots": slots},
    )

def register_thanks(request):
    reg_id = request.session.get("last_registration_id")
    reg = None
    if reg_id:
        reg = (
            Registration.objects
            .select_related("slot")
            .filter(pk=reg_id)
            .first()
        )
    return render(request, "exhibitionpages/register_thanks.html", {"reg": reg})
