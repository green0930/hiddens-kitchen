from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from menu.models import MenuItem

from .forms import OrderForm
from .models import Order, OrderItem


class OrderFormTests(TestCase):
    def setUp(self):
        self.fixed_now = timezone.make_aware(
            datetime(2026, 8, 27, 12, 0),
            timezone.get_current_timezone(),
        )

    @patch("orders.forms.timezone.now")
    def test_phone_or_email_is_required(self, mock_now):
        mock_now.return_value = self.fixed_now

        form = OrderForm(
            data={
                "customer_name": "Test Customer",
                "phone": "",
                "email": "",
                "pickup_date": "2026-08-29",
                "pickup_time": "12:00",
                "notes": "",
            }
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "Please provide either a phone number or an email address.",
            form.non_field_errors(),
        )

    @patch("orders.forms.timezone.now")
    def test_pickup_less_than_24_hours_is_rejected(
        self,
        mock_now,
    ):
        mock_now.return_value = self.fixed_now

        form = OrderForm(
            data={
                "customer_name": "Test Customer",
                "phone": "3105551234",
                "email": "",
                "pickup_date": "2026-08-28",
                "pickup_time": "11:00",
                "notes": "",
            }
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "Pickup must be scheduled at least 24 hours in advance.",
            form.errors["pickup_date"],
        )

    @patch("orders.forms.timezone.now")
    def test_pickup_more_than_24_hours_is_valid(
        self,
        mock_now,
    ):
        mock_now.return_value = self.fixed_now

        form = OrderForm(
            data={
                "customer_name": "Test Customer",
                "phone": "3105551234",
                "email": "",
                "pickup_date": "2026-08-28",
                "pickup_time": "12:30",
                "notes": "",
            }
        )

        self.assertTrue(form.is_valid())


class OrderModelTests(TestCase):
    def setUp(self):
        self.menu_item = MenuItem.objects.create(
            name="Bulgogi Kimbap",
            slug="bulgogi-kimbap",
            description="Fresh bulgogi kimbap.",
            price=Decimal("12.00"),
            category=MenuItem.Category.KIMBAP,
            is_available=True,
        )

        self.order = Order.objects.create(
            customer_name="Test Customer",
            phone="3105551234",
            pickup_date="2026-08-30",
            pickup_time="12:00",
        )

    def test_new_order_defaults_to_pending(self):
        self.assertEqual(
            self.order.status,
            Order.Status.PENDING,
        )

    def test_order_item_line_total(self):
        order_item = OrderItem.objects.create(
            order=self.order,
            menu_item=self.menu_item,
            quantity=3,
            unit_price=Decimal("12.00"),
        )

        self.assertEqual(
            order_item.line_total,
            Decimal("36.00"),
        )


class PreorderViewTests(TestCase):
    def setUp(self):
        self.fixed_now = timezone.make_aware(
            datetime(2026, 8, 27, 12, 0),
            timezone.get_current_timezone(),
        )

        self.menu_item = MenuItem.objects.create(
            name="Bulgogi Kimbap",
            slug="bulgogi-kimbap",
            description="Fresh bulgogi kimbap.",
            price=Decimal("12.00"),
            category=MenuItem.Category.KIMBAP,
            is_available=True,
        )

        self.preorder_url = reverse(
            "orders:preorder"
        )

    def build_order_data(
        self,
        quantity,
        pickup_date,
        pickup_time,
        email="customer@example.com",
        phone="",
    ):
        return {
            "customer_name": "Test Customer",
            "phone": phone,
            "email": email,
            "pickup_date": pickup_date,
            "pickup_time": pickup_time,
            "notes": "",
            f"quantity_{self.menu_item.id}": str(quantity),
        }

    @patch(
        "orders.views.send_customer_request_confirmation"
    )
    @patch(
        "orders.views.send_business_order_notification"
    )
    @patch("orders.views.timezone.now")
    def test_valid_order_creates_order_and_order_item(
        self,
        mock_now,
        mock_business_email,
        mock_customer_email,
    ):
        mock_now.return_value = self.fixed_now

        response = self.client.post(
            self.preorder_url,
            data=self.build_order_data(
                quantity=2,
                pickup_date="2026-08-29",
                pickup_time="12:00",
            ),
        )

        self.assertEqual(
            Order.objects.count(),
            1,
        )

        self.assertEqual(
            OrderItem.objects.count(),
            1,
        )

        order = Order.objects.get()

        order_item = OrderItem.objects.get()

        self.assertEqual(
            order.status,
            Order.Status.PENDING,
        )

        self.assertEqual(
            order_item.quantity,
            2,
        )

        self.assertEqual(
            order_item.unit_price,
            Decimal("12.00"),
        )

        self.assertEqual(
            order_item.line_total,
            Decimal("24.00"),
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:success",
                kwargs={
                    "order_id": order.id,
                },
            ),
        )

        mock_business_email.assert_called_once_with(
            order
        )

        mock_customer_email.assert_called_once_with(
            order
        )

    @patch("orders.views.timezone.now")
    def test_order_without_items_is_rejected(
        self,
        mock_now,
    ):
        mock_now.return_value = self.fixed_now

        response = self.client.post(
            self.preorder_url,
            data=self.build_order_data(
                quantity=0,
                pickup_date="2026-08-29",
                pickup_time="12:00",
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

        self.assertContains(
            response,
            "Please select at least one menu item.",
        )

    @patch("orders.views.timezone.now")
    @patch("orders.forms.timezone.now")
    def test_large_order_less_than_72_hours_is_rejected(
        self,
        mock_form_now,
        mock_view_now,
    ):
        mock_form_now.return_value = self.fixed_now
        mock_view_now.return_value = self.fixed_now

        response = self.client.post(
            self.preorder_url,
            data=self.build_order_data(
                quantity=10,
                pickup_date="2026-08-30",
                pickup_time="11:00",
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

        self.assertContains(
            response,
            "Orders of 10 or more items require "
            "at least 72 hours notice.",
        )

    @patch(
        "orders.views.send_customer_request_confirmation"
    )
    @patch(
        "orders.views.send_business_order_notification"
    )
    @patch("orders.views.timezone.now")
    @patch("orders.forms.timezone.now")
    def test_large_order_more_than_72_hours_is_valid(
        self,
        mock_form_now,
        mock_view_now,
        mock_business_email,
        mock_customer_email,
    ):
        mock_form_now.return_value = self.fixed_now
        mock_view_now.return_value = self.fixed_now

        response = self.client.post(
            self.preorder_url,
            data=self.build_order_data(
                quantity=10,
                pickup_date="2026-08-30",
                pickup_time="12:30",
            ),
        )

        self.assertEqual(
            Order.objects.count(),
            1,
        )

        order = Order.objects.get()

        self.assertEqual(
            order.items.get().quantity,
            10,
        )

        self.assertRedirects(
            response,
            reverse(
                "orders:success",
                kwargs={
                    "order_id": order.id,
                },
            ),
        )

    @patch(
        "orders.views.send_customer_request_confirmation"
    )
    @patch(
        "orders.views.send_business_order_notification"
    )
    @patch("orders.views.timezone.now")
    def test_order_with_phone_and_no_email_is_allowed(
        self,
        mock_now,
        mock_business_email,
        mock_customer_email,
    ):
        mock_now.return_value = self.fixed_now

        response = self.client.post(
            self.preorder_url,
            data=self.build_order_data(
                quantity=1,
                pickup_date="2026-08-29",
                pickup_time="12:00",
                email="",
                phone="3105551234",
            ),
        )

        self.assertEqual(
            Order.objects.count(),
            1,
        )

        order = Order.objects.get()

        self.assertRedirects(
            response,
            reverse(
                "orders:success",
                kwargs={
                    "order_id": order.id,
                },
            ),
        )

        mock_business_email.assert_called_once_with(
            order
        )

        mock_customer_email.assert_not_called()

    @patch(
        "orders.views.send_customer_request_confirmation"
    )
    @patch(
        "orders.views.send_business_order_notification"
    )
    @patch("orders.views.timezone.now")
    def test_order_keeps_price_at_time_of_purchase(
        self,
        mock_now,
        mock_business_email,
        mock_customer_email,
    ):
        mock_now.return_value = self.fixed_now

        self.client.post(
            self.preorder_url,
            data=self.build_order_data(
                quantity=2,
                pickup_date="2026-08-29",
                pickup_time="12:00",
            ),
        )

        order_item = OrderItem.objects.get()

        self.menu_item.price = Decimal("15.00")
        self.menu_item.save()

        order_item.refresh_from_db()

        self.assertEqual(
            order_item.unit_price,
            Decimal("12.00"),
        )

        self.assertEqual(
            order_item.line_total,
            Decimal("24.00"),
        )