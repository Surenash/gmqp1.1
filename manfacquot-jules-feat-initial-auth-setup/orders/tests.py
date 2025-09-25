import uuid
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta, date

from accounts.models import User, UserRole
from designs.models import Design, DesignStatus as DesignModelStatus
from quotes.models import Quote, QuoteStatus
from .models import Order, OrderStatus


class OrderModelTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(email="ordertestcust@example.com", password="password", role=UserRole.CUSTOMER)
        cls.manufacturer = User.objects.create_user(email="ordertestmf@example.com", password="password", role=UserRole.MANUFACTURER)
        cls.design = Design.objects.create(customer=cls.customer, design_name="Order Test Design", material="PLA", quantity=1, status=DesignModelStatus.ANALYSIS_COMPLETE) # Changed to ANALYSIS_COMPLETE for quote

        # Quote needs to be accepted for an order to be typically based on it.
        # However, for model testing, we might create an order directly with a quote.
        # For order creation logic test via Quote update, that's in quotes/tests.py
        cls.quote = Quote.objects.create(
            design=cls.design, manufacturer=cls.manufacturer, price_usd="100.00",
            estimated_lead_time_days=5, status=QuoteStatus.ACCEPTED # Mark as accepted for realism
        )

    def test_order_str_representation(self):
        order = Order.objects.create(
            design=self.design, accepted_quote=self.quote, customer=self.customer, manufacturer=self.manufacturer,
            order_total_price_usd=self.quote.price_usd
        )
        expected_str = f"Order {order.id} for Design '{self.design.design_name}'"
        self.assertEqual(str(order), expected_str)

    def test_calculate_and_set_estimated_delivery(self):
        # Simulate an order that hasn't had its created_at field set yet (i.e., before first save)
        order_pre_save = Order(
            design=self.design, accepted_quote=self.quote, customer=self.customer,
            manufacturer=self.manufacturer, order_total_price_usd=self.quote.price_usd
        )
        # Manually set created_at to a known value for predictable test, as timezone.now() is dynamic
        # However, the method is designed to use timezone.now() if created_at is None

        # Test with lead time from quote
        order_pre_save.calculate_and_set_estimated_delivery() # Uses self.quote.estimated_lead_time_days
        expected_date_from_quote = timezone.now().date() + timedelta(days=self.quote.estimated_lead_time_days)
        self.assertEqual(order_pre_save.estimated_delivery_date, expected_date_from_quote)

        # Test with explicit lead time passed
        order_pre_save.calculate_and_set_estimated_delivery(quote_lead_time_days=10)
        expected_date_explicit = timezone.now().date() + timedelta(days=10)
        self.assertEqual(order_pre_save.estimated_delivery_date, expected_date_explicit)

        # Test after save (created_at is populated)
        order_post_save = Order.objects.create(
            design=self.design, accepted_quote=self.quote, customer=self.customer,
            manufacturer=self.manufacturer, order_total_price_usd=self.quote.price_usd
        ) # created_at is set now
        order_post_save.calculate_and_set_estimated_delivery()
        expected_date_after_save = order_post_save.created_at.date() + timedelta(days=self.quote.estimated_lead_time_days)
        self.assertEqual(order_post_save.estimated_delivery_date, expected_date_after_save)


class OrderAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer1 = User.objects.create_user(email="ordercust1@example.com", password="password", role=UserRole.CUSTOMER, company_name="Cust1Co")
        cls.manufacturer1 = User.objects.create_user(email="ordermf1@example.com", password="password", role=UserRole.MANUFACTURER, company_name="Manuf1Co")
        cls.customer2 = User.objects.create_user(email="ordercust2@example.com", password="password", role=UserRole.CUSTOMER, company_name="Cust2Co")
        cls.admin_user = User.objects.create_superuser(email="orderadmin@example.com", password="password", company_name="OrderAdmin")

        design1 = Design.objects.create(customer=cls.customer1, design_name="Order Design 1", material="ABS", quantity=10, status=DesignModelStatus.ORDERED)
        quote1 = Quote.objects.create(design=design1, manufacturer=cls.manufacturer1, price_usd="120.50", estimated_lead_time_days=7, status=QuoteStatus.ACCEPTED)
        cls.order1_c1_m1 = Order.objects.create(
            design=design1, accepted_quote=quote1, customer=cls.customer1, manufacturer=cls.manufacturer1,
            order_total_price_usd=quote1.price_usd, status=OrderStatus.PENDING_PAYMENT
        )
        cls.order1_c1_m1.calculate_and_set_estimated_delivery()
        cls.order1_c1_m1.save()

        design2 = Design.objects.create(customer=cls.customer2, design_name="Order Design 2", material="PLA", quantity=5, status=DesignModelStatus.ORDERED)
        quote2 = Quote.objects.create(design=design2, manufacturer=cls.manufacturer1, price_usd="80.00", estimated_lead_time_days=3, status=QuoteStatus.ACCEPTED)
        cls.order2_c2_m1 = Order.objects.create(
            design=design2, accepted_quote=quote2, customer=cls.customer2, manufacturer=cls.manufacturer1,
            order_total_price_usd=quote2.price_usd, status=OrderStatus.IN_PRODUCTION
        )
        cls.order2_c2_m1.calculate_and_set_estimated_delivery()
        cls.order2_c2_m1.save()

    def _login(self, user_obj):
        self.client.force_authenticate(user=user_obj)

    def test_customer_list_own_orders(self):
        self._login(self.customer1)
        url = reverse('order_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(uuid.UUID(response.data[0]['id']), self.order1_c1_m1.id)

    def test_manufacturer_list_received_orders(self):
        self._login(self.manufacturer1)
        url = reverse('order_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 2)
        order_ids_in_response = {uuid.UUID(item['id']) for item in response.data}
        self.assertIn(self.order1_c1_m1.id, order_ids_in_response)
        self.assertIn(self.order2_c2_m1.id, order_ids_in_response)

    def test_admin_list_all_orders(self):
        self._login(self.admin_user)
        url = reverse('order_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data), 2)

    def test_list_orders_unauthenticated(self):
        self.client.logout()
        url = reverse('order_list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_retrieve_own_order_detail(self):
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(uuid.UUID(response.data['id']), self.order1_c1_m1.id)
        self.assertEqual(response.data['customer_info']['id'], self.customer1.id) # Compare UUIDs

    def test_manufacturer_retrieve_received_order_detail(self):
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(uuid.UUID(response.data['id']), self.order1_c1_m1.id)
        self.assertEqual(response.data['manufacturer_info']['id'], self.manufacturer1.id) # Compare UUIDs

    def test_admin_retrieve_any_order_detail(self):
        self._login(self.admin_user)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(uuid.UUID(response.data['id']), self.order1_c1_m1.id)

    def test_user_cannot_retrieve_unrelated_order(self):
        # customer2 did not place order1_c1_m1, nor is manufacturer for it
        unrelated_manufacturer = User.objects.create_user(email="othermf@example.com", password="pw", role=UserRole.MANUFACTURER)
        self._login(unrelated_manufacturer)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_retrieve_order_unauthenticated(self):
        self.client.logout()
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Order Update Tests (Status, Tracking by Manufacturer) ---
    def test_manufacturer_update_order_status_manuf_confirm_to_processing(self): # Renamed for clarity
        self.order1_c1_m1.status = OrderStatus.PENDING_MANUFACTURER_CONFIRMATION
        self.order1_c1_m1.save()
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"status": OrderStatus.PROCESSING.value}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.order1_c1_m1.refresh_from_db()
        self.assertEqual(self.order1_c1_m1.status, OrderStatus.PROCESSING)

    def test_manufacturer_update_order_status_processing_to_in_production(self):
        self.order1_c1_m1.status = OrderStatus.PROCESSING
        self.order1_c1_m1.save()
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"status": OrderStatus.IN_PRODUCTION.value}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.order1_c1_m1.refresh_from_db()
        self.assertEqual(self.order1_c1_m1.status, OrderStatus.IN_PRODUCTION)

    def test_manufacturer_update_order_status_in_production_to_shipped(self):
        self.order1_c1_m1.status = OrderStatus.IN_PRODUCTION
        self.order1_c1_m1.save()
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        tracking_data = {"tracking_number": "123XYZ", "shipping_carrier": "FedUp"}
        data = {"status": OrderStatus.SHIPPED.value, **tracking_data}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.order1_c1_m1.refresh_from_db()
        self.assertEqual(self.order1_c1_m1.status, OrderStatus.SHIPPED)
        self.assertEqual(self.order1_c1_m1.tracking_number, tracking_data["tracking_number"])
        self.assertEqual(self.order1_c1_m1.shipping_carrier, tracking_data["shipping_carrier"])
        self.assertEqual(self.order1_c1_m1.actual_ship_date, timezone.now().date()) # Auto-set by serializer

    def test_manufacturer_invalid_status_transition(self):
        self.order1_c1_m1.status = OrderStatus.PENDING_MANUFACTURER_CONFIRMATION
        self.order1_c1_m1.save()
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"status": OrderStatus.SHIPPED.value} # Invalid: PENDING_MANUF_CONFIRM -> SHIPPED
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertIn("Invalid status transition", response.data.get("detail", ""))

    def test_manufacturer_update_tracking_info(self):
        self.order1_c1_m1.status = OrderStatus.SHIPPED # Assume it's already shipped
        self.order1_c1_m1.save()
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"tracking_number": "NEWTRACK123", "shipping_carrier": "UPS"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.order1_c1_m1.refresh_from_db()
        self.assertEqual(self.order1_c1_m1.tracking_number, "NEWTRACK123")
        self.assertEqual(self.order1_c1_m1.shipping_carrier, "UPS")

    # --- Order Update Tests (Status, Shipping Address by Customer) ---
    def test_customer_cancel_order_success(self):
        self.order1_c1_m1.status = OrderStatus.PROCESSING # A cancelable state
        self.order1_c1_m1.save()
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"status": OrderStatus.CANCELLED_BY_CUSTOMER.value, "cancellation_reason": "Changed my mind."}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.order1_c1_m1.refresh_from_db()
        self.assertEqual(self.order1_c1_m1.status, OrderStatus.CANCELLED_BY_CUSTOMER)
        self.assertEqual(self.order1_c1_m1.cancellation_reason, "Changed my mind.")

    def test_customer_cancel_order_missing_reason_fail(self):
        self.order1_c1_m1.status = OrderStatus.PROCESSING
        self.order1_c1_m1.save()
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"status": OrderStatus.CANCELLED_BY_CUSTOMER.value} # Missing reason
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Permission check
        self.assertIn("Please provide a reason", response.data.get("detail", ""))


    def test_customer_cannot_cancel_shipped_order(self):
        self.order1_c1_m1.status = OrderStatus.SHIPPED
        self.order1_c1_m1.save()
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"status": OrderStatus.CANCELLED_BY_CUSTOMER.value, "cancellation_reason": "Too late."}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertIn("cannot be cancelled by customer in its current status", response.data.get("detail", ""))

    def test_customer_update_shipping_address_success(self):
        self.order1_c1_m1.status = OrderStatus.PROCESSING # Allowed state
        self.order1_c1_m1.save()
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        new_address = {"street1": "123 New St", "city": "New City", "zip_code": "90210"}
        data = {"shipping_address": new_address}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.order1_c1_m1.refresh_from_db()
        self.assertEqual(self.order1_c1_m1.shipping_address, new_address)

    def test_customer_cannot_update_shipping_address_if_shipped(self):
        self.order1_c1_m1.status = OrderStatus.SHIPPED
        self.order1_c1_m1.save()
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        new_address = {"street1": "123 New St", "city": "New City", "zip_code": "90210"}
        data = {"shipping_address": new_address}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertIn("Shipping address cannot be updated", response.data.get("detail", ""))

    # --- Permission Denials for Updates ---
    def test_customer_cannot_update_tracking_info(self):
        self._login(self.customer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        data = {"tracking_number": "CUST_TRACK_FAIL"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Customer cannot update field: tracking_number", response.data.get("detail", ""))

    def test_manufacturer_cannot_update_shipping_address_normally(self):
        # (Unless specific logic allows it, current permission restricts it)
        self._login(self.manufacturer1)
        url = reverse('order_detail', kwargs={'id': self.order1_c1_m1.id})
        new_address = {"street1": "MF Trying St"}
        data = {"shipping_address": new_address}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Manufacturer cannot update field: shipping_address", response.data.get("detail", ""))
