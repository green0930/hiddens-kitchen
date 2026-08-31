from django.conf import settings
from django.core.mail import send_mail


def get_order_details(order):
    items = order.items.select_related("menu_item").all()

    total = sum(
        item.line_total
        for item in items
    )

    item_lines = [
        (
            f"{item.menu_item.name} x {item.quantity} "
            f"- ${item.line_total:.2f}"
        )
        for item in items
    ]

    return items, total, item_lines


def send_business_order_notification(order):
    _, total, item_lines = get_order_details(order)

    message = "\n".join(
        [
            "New Hidden's Kitchen pre-order request",
            "",
            f"Request #: {order.id}",
            f"Customer: {order.customer_name}",
            f"Phone: {order.phone or '-'}",
            f"Email: {order.email or '-'}",
            "",
            "Items:",
            *item_lines,
            "",
            f"Order Total: ${total:.2f}",
            (
                "Pickup: "
                f"{order.pickup_date.strftime('%B %d, %Y')} "
                f"at {order.pickup_time.strftime('%I:%M %p')}"
            ),
            "",
            f"Notes: {order.notes or '-'}",
            "",
            "Status: Pending",
        ]
    )

    _send_email(
        subject=f"New Hidden's Kitchen Order #{order.id}",
        message=message,
        recipient=settings.ORDER_NOTIFICATION_EMAIL,
        error_label=f"Order #{order.id} business notification",
    )


def send_customer_request_confirmation(order):
    if not order.email:
        return

    _, total, item_lines = get_order_details(order)

    message = "\n".join(
        [
            f"Hi {order.customer_name},",
            "",
            "Thank you for your pre-order request from Hidden's Kitchen.",
            "",
            f"Request #: {order.id}",
            "",
            "Your order:",
            *item_lines,
            "",
            f"Order Total: ${total:.2f}",
            (
                "Requested Pickup: "
                f"{order.pickup_date.strftime('%B %d, %Y')} "
                f"at {order.pickup_time.strftime('%I:%M %p')}"
            ),
            "",
            "Your order is not confirmed yet.",
            (
                "I will review availability and contact you "
                "to confirm your order."
            ),
            (
                "Prepayment via Zelle is required after "
                "availability is confirmed."
            ),
            "",
            "Hidden's Kitchen",
        ]
    )

    _send_email(
        subject=f"Hidden's Kitchen Pre-order Request #{order.id}",
        message=message,
        recipient=order.email,
        error_label=f"Order #{order.id} customer confirmation",
    )


def send_order_confirmed_email(order):
    if not order.email:
        return

    _, total, item_lines = get_order_details(order)

    payment_url = (
        f"{settings.SITE_URL}"
        f"/order/payment/{order.payment_token}/"
    )

    message = "\n".join(
        [
            f"Hi {order.customer_name},",
            "",
            (
                "Your Hidden's Kitchen order is available "
                "for the requested pickup time."
            ),
            "",
            f"Order #{order.id}",
            "",
            "Your order:",
            *item_lines,
            "",
            f"Order Total: ${total:.2f}",
            (
                "Pickup: "
                f"{order.pickup_date.strftime('%B %d, %Y')} "
                f"at {order.pickup_time.strftime('%I:%M %p')}"
            ),
            "",
            "The next step is prepayment via Zelle.",
            "",
            "View your secure payment details and QR code:",
            payment_url,
            "",
            (
                "Your order will be fully confirmed once "
                "payment is received."
            ),
            "",
            "Thank you!",
            "Hidden's Kitchen",
        ]
    )

    _send_email(
        subject=(
            f"Hidden's Kitchen Order #{order.id} "
            "- Availability Confirmed"
        ),
        message=message,
        recipient=order.email,
        error_label=f"Order #{order.id} confirmed email",
    )


def send_payment_received_email(order):
    if not order.email:
        return

    _, total, item_lines = get_order_details(order)

    message = "\n".join(
        [
            f"Hi {order.customer_name},",
            "",
            "Payment received. Thank you!",
            "",
            "Your Hidden's Kitchen order is now fully confirmed.",
            "",
            f"Order #{order.id}",
            "",
            "Your order:",
            *item_lines,
            "",
            f"Order Total: ${total:.2f}",
            (
                "Pickup: "
                f"{order.pickup_date.strftime('%B %d, %Y')} "
                f"at {order.pickup_time.strftime('%I:%M %p')}"
            ),
            "",
            (
                "Your food will be prepared fresh for your "
                "confirmed pickup time."
            ),
            "",
            "Thank you!",
            "Hidden's Kitchen",
        ]
    )

    _send_email(
        subject=f"Hidden's Kitchen Order #{order.id} - Payment Received",
        message=message,
        recipient=order.email,
        error_label=f"Order #{order.id} payment email",
    )


def send_order_ready_email(order):
    if not order.email:
        return

    _, total, item_lines = get_order_details(order)

    message = "\n".join(
        [
            f"Hi {order.customer_name},",
            "",
            "Your Hidden's Kitchen order is ready for pickup!",
            "",
            f"Order #{order.id}",
            "",
            "Your order:",
            *item_lines,
            "",
            f"Order Total: ${total:.2f}",
            (
                "Pickup: "
                f"{order.pickup_date.strftime('%B %d, %Y')} "
                f"at {order.pickup_time.strftime('%I:%M %p')}"
            ),
            "",
            "Thank you for ordering from Hidden's Kitchen.",
            "See you soon!",
            "",
            "Hidden's Kitchen",
        ]
    )

    _send_email(
        subject=f"Hidden's Kitchen Order #{order.id} - Ready for Pickup",
        message=message,
        recipient=order.email,
        error_label=f"Order #{order.id} ready email",
    )


def send_order_cancelled_email(order):
    if not order.email:
        return

    _, total, item_lines = get_order_details(order)

    message = "\n".join(
        [
            f"Hi {order.customer_name},",
            "",
            "Your Hidden's Kitchen order has been cancelled.",
            "",
            f"Order #{order.id}",
            "",
            "Order details:",
            *item_lines,
            "",
            f"Order Total: ${total:.2f}",
            (
                "Pickup: "
                f"{order.pickup_date.strftime('%B %d, %Y')} "
                f"at {order.pickup_time.strftime('%I:%M %p')}"
            ),
            "",
            (
                "If you have any questions about this cancellation, "
                "please contact Hidden's Kitchen."
            ),
            "",
            "Hidden's Kitchen",
        ]
    )

    _send_email(
        subject=f"Hidden's Kitchen Order #{order.id} - Cancelled",
        message=message,
        recipient=order.email,
        error_label=f"Order #{order.id} cancellation email",
    )


def _send_email(
    subject,
    message,
    recipient,
    error_label,
):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )

    except Exception as exc:
        print(
            f"{error_label} failed: {exc}"
        )