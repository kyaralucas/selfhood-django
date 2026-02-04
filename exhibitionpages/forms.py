from django import forms
from .models import Registration, TimeSlot

from django import forms
from .models import Registration, TimeSlot

class RegistrationForm(forms.ModelForm):
    guests = forms.ChoiceField(
        choices=[(1, "1"), (2, "2")],
        initial=1,
        required=True,
        label="Guests",
        widget=forms.Select()
    )

    prompt_answer = forms.CharField(
        required=False,
        max_length=1000, 
        label="(Optional) Your answer",
        widget=forms.Textarea(attrs={
            "rows": 3,
            "maxlength": 1000,  
            "placeholder": "Answer with one word or a short phrase. Will be added anonymously to digital resting space."
        })
    )

    slot = forms.ModelChoiceField(
        queryset=TimeSlot.objects.none(),
        empty_label=None,
        widget=forms.RadioSelect
    )

    class Meta:
        model = Registration
        fields = ["name", "email", "guests", "slot", "prompt_answer"] 
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slot"].queryset = TimeSlot.objects.order_by("time")

