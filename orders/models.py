import uuid

from django.db import models

from menu.models import MenuItem


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PAID = "paid", "Paid"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready for Pickup"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    payment_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    customer_name = models.CharField(
        max_length=120,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    pickup_date = models.DateField()

    pickup_time = models.TimeField()

    notes = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return f"{self.customer_name} - {self.pickup_date}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    unit_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price