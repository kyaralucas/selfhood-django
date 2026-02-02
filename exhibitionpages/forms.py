from django import forms
from .models import Registration, TimeSlot

class RegistrationForm(forms.ModelForm):
    prompt_answer = forms.CharField(
        required=False,
        label="(Optional) Your answer",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "One word or a short phrase. Will be added anonymously to digital resting space."})
    )

    slot = forms.ModelChoiceField(
        queryset=TimeSlot.objects.none(),  # set in __init__
        empty_label=None,
        widget=forms.RadioSelect
    )

    class Meta:
        model = Registration
        fields = ["name", "email", "guests", "slot", "prompt_answer"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "guests": forms.NumberInput(attrs={"min": 0, "max": 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always show slots in chronological order
        self.fields["slot"].queryset = TimeSlot.objects.order_by("time")
