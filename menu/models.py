from django.db import models


class MenuItem(models.Model):
    class Category(models.TextChoices):
        KIMBAP = "kimbap", "Kimbap"
        NOODLES = "noodles", "Noodles"
        RICE_BOWL = "rice_bowl", "Rice Bowl"
        STREET_FOOD = "street_food", "Street Food"
        SOUP = "soup", "Soup & Stew"
        PANCAKE = "pancake", "Pancake"
        OTHER = "other", "Other"

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
    )

    is_available = models.BooleanField(
        default=True,
    )

    is_featured = models.BooleanField(
        default=False,
        help_text="Show this item in the featured menu on the homepage.",
    )

    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]

    def __str__(self):
        return self.name