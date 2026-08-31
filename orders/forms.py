from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

from .models import Order


PICKUP_TIME_CHOICES = [
    ("", "Choose a pickup time"),
    ("11:00", "11:00 AM"),
    ("11:30", "11:30 AM"),
    ("12:00", "12:00 PM"),
    ("12:30", "12:30 PM"),
    ("13:00", "1:00 PM"),
    ("13:30", "1:30 PM"),
    ("14:00", "2:00 PM"),
    ("14:30", "2:30 PM"),
    ("15:00", "3:00 PM"),
    ("15:30", "3:30 PM"),
    ("16:00", "4:00 PM"),
    ("16:30", "4:30 PM"),
    ("17:00", "5:00 PM"),
    ("17:30", "5:30 PM"),
    ("18:00", "6:00 PM"),
]


class OrderForm(forms.ModelForm):
    pickup_time = forms.ChoiceField(
        choices=PICKUP_TIME_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label="Pickup time",
    )

    class Meta:
        model = Order

        fields = (
            "customer_name",
            "phone",
            "email",
            "pickup_date",
            "pickup_time",
            "notes",
        )

        widgets = {
            "customer_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your name",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Email address",
                }
            ),
            "pickup_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Allergies, special requests, "
                        "or anything else I should know"
                    ),
                    "rows": 4,
                }
            ),
        }

        labels = {
            "customer_name": "Name",
            "phone": "Phone",
            "email": "Email",
            "pickup_date": "Pickup date",
            "notes": "Notes",
        }

        help_texts = {
            "phone": "Phone or email is required so I can confirm your order.",
            "email": "Phone or email is required so I can confirm your order.",
        }

    def clean(self):
        cleaned_data = super().clean()

        phone = cleaned_data.get("phone")
        email = cleaned_data.get("email")
        pickup_date = cleaned_data.get("pickup_date")
        pickup_time_value = cleaned_data.get("pickup_time")

        if not phone and not email:
            raise forms.ValidationError(
                "Please provide either a phone number or an email address."
            )

        if pickup_date and pickup_time_value:
            pickup_time = datetime.strptime(
                pickup_time_value,
                "%H:%M",
            ).time()

            pickup_datetime = datetime.combine(
                pickup_date,
                pickup_time,
            )

            current_timezone = timezone.get_current_timezone()

            pickup_datetime = timezone.make_aware(
                pickup_datetime,
                current_timezone,
            )

            minimum_pickup_datetime = (
                timezone.now() + timedelta(hours=24)
            )

            if pickup_datetime < minimum_pickup_datetime:
                self.add_error(
                    "pickup_date",
                    "Pickup must be scheduled at least 24 hours in advance.",
                )

        return cleaned_data