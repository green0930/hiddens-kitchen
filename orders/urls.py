from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [
    path(
        "",
        views.preorder,
        name="preorder",
    ),
    path(
        "success/<int:order_id>/",
        views.order_success,
        name="success",
    ),
    path(
        "payment/<uuid:payment_token>/",
        views.payment_details,
        name="payment_details",
    ),
    path(
        "payment/<uuid:payment_token>/qr/",
        views.payment_qr,
        name="payment_qr",
    ),
]