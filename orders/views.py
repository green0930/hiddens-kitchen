import base64
from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from menu.models import MenuItem

from .emails import (
    send_business_order_notification,
    send_customer_request_confirmation,
)
from .forms import OrderForm
from .models import Order, OrderItem


@transaction.atomic
def preorder(request):
    available_items = list(
        MenuItem.objects.filter(
            is_available=True,
        )
    )

    if request.method == "POST":
        form = OrderForm(request.POST)

        selected_items = []
        total_quantity = 0

        for item in available_items:
            quantity_value = request.POST.get(
                f"quantity_{item.id}",
                "0",
            )

            try:
                quantity = int(quantity_value)
            except (TypeError, ValueError):
                quantity = 0

            quantity = max(quantity, 0)
            item.order_quantity = quantity

            if quantity > 0:
                selected_items.append(
                    {
                        "menu_item": item,
                        "quantity": quantity,
                    }
                )

                total_quantity += quantity

        if not selected_items:
            form.add_error(
                None,
                "Please select at least one menu item.",
            )

        if form.is_valid() and selected_items:
            pickup_date = form.cleaned_data["pickup_date"]

            pickup_time = datetime.strptime(
                form.cleaned_data["pickup_time"],
                "%H:%M",
            ).time()

            pickup_datetime = datetime.combine(
                pickup_date,
                pickup_time,
            )

            pickup_datetime = timezone.make_aware(
                pickup_datetime,
                timezone.get_current_timezone(),
            )

            if total_quantity >= 10:
                minimum_pickup = (
                    timezone.now()
                    + timedelta(hours=72)
                )

                if pickup_datetime < minimum_pickup:
                    form.add_error(
                        "pickup_date",
                        (
                            "Orders of 10 or more items require "
                            "at least 72 hours notice."
                        ),
                    )

            if not form.errors:
                order = form.save(
                    commit=False,
                )

                order.status = Order.Status.PENDING
                order.save()

                for selected in selected_items:
                    menu_item = selected["menu_item"]
                    quantity = selected["quantity"]

                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=quantity,
                        unit_price=Decimal(
                            str(menu_item.price)
                        ),
                    )

                send_business_order_notification(order)

                if order.email:
                    send_customer_request_confirmation(order)

                return redirect(
                    "orders:success",
                    payment_token=order.payment_token,
                )

    else:
        form = OrderForm()

        for item in available_items:
            item.order_quantity = 0

    grouped_items = OrderedDict()

    for category_value, category_label in MenuItem.Category.choices:
        category_items = [
            item
            for item in available_items
            if item.category == category_value
        ]

        if category_items:
            grouped_items[category_label] = category_items

    context = {
        "form": form,
        "grouped_items": grouped_items,
    }

    return render(
        request,
        "orders/preorder.html",
        context,
    )


def order_success(request, payment_token):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__menu_item"
        ),
        payment_token=payment_token,
    )

    total = sum(
        item.line_total
        for item in order.items.all()
    )

    context = {
        "order": order,
        "total": total,
    }

    return render(
        request,
        "orders/order_success.html",
        context,
    )


def payment_details(request, payment_token):
    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items__menu_item"
        ),
        payment_token=payment_token,
    )

    total = sum(
        item.line_total
        for item in order.items.all()
    )

    context = {
        "order": order,
        "total": total,
    }

    return render(
        request,
        "orders/payment_details.html",
        context,
    )

def payment_qr(request, payment_token):
    get_object_or_404(
        Order,
        payment_token=payment_token,
    )

    local_qr = (
        settings.BASE_DIR
        / "static"
        / "images"
        / "payment"
        / "zelle-qr.png"
    )

    secret_base64 = Path(
        "/etc/secrets/zelle-qr.b64"
    )

    if secret_base64.exists():
        try:
            qr_data = base64.b64decode(
                secret_base64.read_text().strip()
            )
            
        except Exception:
            raise Http404(
                "Payment QR code is unavailable."
            )

        return HttpResponse(
            qr_data,
            content_type="image/png",
        )

    if local_qr.exists():
        return FileResponse(
            open(local_qr, "rb"),
            content_type="image/png",
        )

    raise Http404(
        "Payment QR code is unavailable."
    )