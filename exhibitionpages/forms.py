from django import forms
from .models import Registration, TimeSlot

class RegistrationForm(forms.ModelForm):
    prompt_answer = forms.CharField(
        required=False,
        label="(Optional) Your answer",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "If you'd like…"})
    )

    slot = forms.ModelChoiceField(
        queryset=TimeSlot.objects.none(),
        empty_label=None,
        widget=forms.RadioSelect
    )

    class Meta:
        model = Registration
        fields = ["name", "email", "slot", "prompt_answer"] 
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Always show slots in chronological order
        self.fields["slot"].queryset = TimeSlot.objects.order_by("time")
