# calendar_rules/forms.py
from django import forms
from .models import PriceRule

class PriceRuleForm(forms.ModelForm):
    confirm_override = forms.BooleanField(
        required=False,
        label="Sovrascrivi regole esistenti",
        help_text="Spunta per sovrascrivere eventuali regole sovrapposte"
    )

    class Meta:
        model = PriceRule
        fields = ['listing', 'start_date', 'end_date', 'price', 'min_nights']