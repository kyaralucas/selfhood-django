import random
from django.shortcuts import render, redirect
from django.db import transaction
from .forms import RegistrationForm, SimpleRegistrationForm
from .models import Registration, TimeSlot, SimpleRegistration
from .questions import QUESTIONS

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib import messages

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

MAX_GUESTS = 30

def simple_register(request):
    total_registered = (
        SimpleRegistration.objects.aggregate(total=Sum("guests"))["total"] or 0
    )
    remaining_spots = max(0, MAX_GUESTS - total_registered)
    sold_out = total_registered >= MAX_GUESTS

    success = False
    registered_name = None
    registered_email = None
    registered_guests = None

    if request.method == "POST":
        if sold_out:
            messages.error(request, "Sorry, this event is sold out.")
            return render(request, "exhibitionpages/simple_register.html", {
                "form": None,
                "sold_out": True,
                "total_registered": total_registered,
                "remaining_spots": 0,
                "max_guests": MAX_GUESTS,
                "success": False,
            })

        form = SimpleRegistrationForm(request.POST)

        if form.is_valid():
            requested_guests = int(form.cleaned_data["guests"])

            with transaction.atomic():
                current_total = (
                    SimpleRegistration.objects.aggregate(total=Sum("guests"))["total"] or 0
                )
                current_remaining = MAX_GUESTS - current_total

                if current_remaining <= 0:
                    messages.error(request, "Sorry, this event just sold out.")
                    return render(request, "exhibitionpages/simple_register.html", {
                        "form": None,
                        "sold_out": True,
                        "total_registered": current_total,
                        "remaining_spots": 0,
                        "max_guests": MAX_GUESTS,
                        "success": False,
                    })

                if requested_guests > current_remaining:
                    form.add_error("guests", f"Only {current_remaining} spot(s) remaining.")
                else:
                    registration = form.save(commit=False)
                    registration.guests = requested_guests
                    registration.save()

                    def send_confirmation_email(registration_id: int):
                        try:
                            reg = SimpleRegistration.objects.get(pk=registration_id)

                            subject = "Your seat is confirmed!"
                            message = render_to_string(
                                "exhibitionpages/emails/registration_confirmation.txt",
                                {
                                    "name": getattr(reg, "name", "there"),
                                },
                            )

                            send_mail(
                                subject=subject,
                                message=message,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[reg.email],
                                fail_silently=False,
                            )

                            logger.info(
                                "Confirmation email sent for registration %s to %s",
                                reg.pk,
                                reg.email,
                            )
                        except Exception:
                            logger.exception(
                                "Confirmation email failed for registration %s",
                                registration_id,
                            )

                    transaction.on_commit(
                        lambda: send_confirmation_email(registration.pk)
                    )

                    logger.info(
                        "Confirmation email scheduled after commit for registration %s",
                        registration.pk,
                    )

                    total_registered = (
                        SimpleRegistration.objects.aggregate(total=Sum("guests"))["total"] or 0
                    )
                    remaining_spots = max(0, MAX_GUESTS - total_registered)
                    sold_out = total_registered >= MAX_GUESTS

                    success = True
                    registered_name = registration.name
                    registered_email = registration.email
                    registered_guests = registration.guests

                    return render(request, "exhibitionpages/simple_register.html", {
                        "form": None,
                        "sold_out": sold_out,
                        "total_registered": total_registered,
                        "remaining_spots": remaining_spots,
                        "max_guests": MAX_GUESTS,
                        "success": success,
                        "registered_name": registered_name,
                        "registered_email": registered_email,
                        "registered_guests": registered_guests,
                    })
    else:
        form = None if sold_out else SimpleRegistrationForm()

    return render(request, "exhibitionpages/simple_register.html", {
        "form": form,
        "sold_out": sold_out,
        "total_registered": total_registered,
        "remaining_spots": remaining_spots,
        "max_guests": MAX_GUESTS,
        "success": success,
        "registered_name": registered_name,
        "registered_email": registered_email,
        "registered_guests": registered_guests,
    })


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

                        subject = "SUBJECT: Your seat is confirmed!"
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
                        logger.info("Confirmation email SENT for registration %s", obj.pk)
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
            SimpleRegistration.objects
            .select_related("slot")
            .filter(pk=reg_id)
            .first()
        )
    return render(request, "exhibitionpages/register_thanks.html", {"reg": reg})

def events(request):
    return render(request, "exhibitionpages/events.html", {})

def letters(request):
    return render(request, "exhibitionpages/letters.html", {})
