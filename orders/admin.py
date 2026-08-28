from django.contrib import admin

from .emails import (
    send_order_confirmed_email,
    send_order_ready_email,
    send_payment_received_email,
    send_order_cancelled_email,
)
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "menu_item",
        "quantity",
        "unit_price",
        "line_total_display",
    )
    can_delete = False

    fields = (
        "menu_item",
        "quantity",
        "unit_price",
        "line_total_display",
    )

    @admin.display(description="Line total")
    def line_total_display(self, obj):
        if not obj.pk:
            return "-"
        return f"${obj.line_total:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "pickup_date",
        "pickup_time",
        "status",
        "order_total_display",
        "created_at",
    )

    list_filter = (
        "status",
        "pickup_date",
        "created_at",
    )

    search_fields = (
        "customer_name",
        "phone",
        "email",
    )

    ordering = (
        "-created_at",
    )


    readonly_fields = (
        "created_at",
        "updated_at",
        "order_total_display",
    )

    inlines = [
        OrderItemInline,
    ]

    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    "customer_name",
                    "phone",
                    "email",
                ),
            },
        ),
        (
            "Pickup",
            {
                "fields": (
                    "pickup_date",
                    "pickup_time",
                ),
            },
        ),
        (
            "Order",
            {
                "fields": (
                    "status",
                    "notes",
                    "order_total_display",
                ),
            },
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Order total")
    def order_total_display(self, obj):
        if not obj.pk:
            return "$0.00"

        total = sum(
            item.line_total
            for item in obj.items.all()
        )

        return f"${total:.2f}"

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        previous_status = None

        if change and obj.pk:
            previous_status = (
                Order.objects
                .filter(pk=obj.pk)
                .values_list("status", flat=True)
                .first()
            )

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        if not obj.email:
            return

        if (
            previous_status != Order.Status.CONFIRMED
            and obj.status == Order.Status.CONFIRMED
        ):
            send_order_confirmed_email(obj)

        if (
            previous_status != Order.Status.PAID
            and obj.status == Order.Status.PAID
        ):
            send_payment_received_email(obj)

        if (
            previous_status != Order.Status.READY
            and obj.status == Order.Status.READY
        ):
            send_order_ready_email(obj)

        if (
            previous_status != Order.Status.CANCELLED
            and obj.status == Order.Status.CANCELLED
        ):
            send_order_cancelled_email(obj)


    def save_formset(
        self,
        request,
        form,
        formset,
        change,
    ):
        instances = formset.save(commit=False)

        for instance in instances:
            instance.save()

        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "menu_item",
        "quantity",
        "unit_price",
        "line_total_display",
    )

    search_fields = (
        "order__customer_name",
        "menu_item__name",
    )

    @admin.display(description="Line total")
    def line_total_display(self, obj):
        return f"${obj.line_total:.2f}"