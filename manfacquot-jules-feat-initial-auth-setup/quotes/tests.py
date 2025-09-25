import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
# from django.conf import settings # Not strictly needed for these tests yet

from accounts.models import User, UserRole
from designs.models import Design, DesignStatus as DesignModelStatus # Renamed to avoid clash
from .models import Quote, QuoteStatus # Current app's models

class QuoteAPITests(APITestCase):

    def setUp(self):
        # Customer 1 (Design Owner)
        self.customer1 = User.objects.create_user(
            email="owner_quotes@example.com", password="Password123!", # Unique email
            company_name="Design Owner Inc.", role=UserRole.CUSTOMER
        )
        # Manufacturer 1 (Quote Creator)
        self.manufacturer1 = User.objects.create_user(
            email="mf1_quotes@example.com", password="Password123!", # Unique email
            company_name="Manuf One Corp", role=UserRole.MANUFACTURER
        )
        # Manufacturer 2 (Another Manufacturer)
        self.manufacturer2 = User.objects.create_user(
            email="mf2_quotes@example.com", password="Password123!", # Unique email
            company_name="Manuf Two Ltd", role=UserRole.MANUFACTURER
        )
        # Admin User
        self.admin_user = User.objects.create_superuser( # Superuser is staff by default
            email="admin_quotes@example.com", password="Password123!", company_name="AdminQuoteCo"
        )


        # Design by Customer 1, ready for quotes
        self.design_c1_analyzed = Design.objects.create(
            customer=self.customer1, design_name="Analyzed Design C1 For Quotes", # Unique name
            s3_file_key="key_quotes1.stl", material="PLA", quantity=10,
            status=DesignModelStatus.ANALYSIS_COMPLETE,
            geometric_data={"volume_cm3": 100}
        )

        # Design by Customer 1, still pending analysis
        self.design_c1_pending = Design.objects.create(
            customer=self.customer1, design_name="Pending Design C1 For Quotes", # Unique name
            s3_file_key="key_quotes2.stl", material="ABS", quantity=5,
            status=DesignModelStatus.PENDING_ANALYSIS
        )

        # Quote by Manufacturer 1 for Customer 1's analyzed design
        self.quote_mf1_design_c1 = Quote.objects.create(
            design=self.design_c1_analyzed,
            manufacturer=self.manufacturer1,
            price_usd="150.00",
            estimated_lead_time_days=10,
            status=QuoteStatus.PENDING
        )

    def _login(self, user_obj):
        # APITestCase's force_authenticate is simpler for direct user object login
        self.client.force_authenticate(user=user_obj)

    # --- Quote Creation Tests (/api/designs/{design_id}/quotes/) ---
    def test_manufacturer_create_quote_success(self):
        self._login(self.manufacturer2)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_analyzed.id})
        data = {
            "price_usd": "200.00",
            "estimated_lead_time_days": 7,
            "notes": "A good quote from MF2"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Quote.objects.count(), 2)
        new_quote = Quote.objects.get(id=response.data['id'])
        self.assertEqual(new_quote.manufacturer, self.manufacturer2)
        self.assertEqual(new_quote.design, self.design_c1_analyzed)
        self.assertEqual(float(new_quote.price_usd), 200.00)

    def test_manufacturer_cannot_quote_own_design(self):
        # Create a design owned by manufacturer1
        # Ensure manufacturer1 has a Manufacturer profile if your setup relies on it for other things
        # from accounts.models import Manufacturer as ManufacturerProfile
        # ManufacturerProfile.objects.get_or_create(user=self.manufacturer1)

        design_mf1 = Design.objects.create(
            customer=self.manufacturer1, # Manufacturer is the customer here
            design_name="MF1 Own Design For Quotes", # Unique name
            s3_file_key="key_mf1_quotes.stl", material="PETG", quantity=1,
            status=DesignModelStatus.ANALYSIS_COMPLETE
        )
        self._login(self.manufacturer1)
        url = reverse('design_quote_list_create', kwargs={'design_id': design_mf1.id})
        data = {"price_usd": "50.00", "estimated_lead_time_days": 3}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertIn("Manufacturers cannot quote their own designs", response.data.get('detail', ''))


    def test_manufacturer_cannot_quote_design_not_analyzed(self):
        self._login(self.manufacturer1)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_pending.id})
        data = {"price_usd": "100.00", "estimated_lead_time_days": 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)
        self.assertIn(f"Design must be in '{DesignModelStatus.ANALYSIS_COMPLETE.label}' status", response.data.get('detail', ''))

    def test_manufacturer_cannot_quote_same_design_twice(self):
        self._login(self.manufacturer1)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_analyzed.id})
        data = {"price_usd": "180.00", "estimated_lead_time_days": 8}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        # The error is raised as ValidationError({"detail": message}) in perform_create
        self.assertEqual(response.data.get('detail'), "You have already submitted a quote for this design.")


    def test_customer_cannot_create_quote(self):
        self._login(self.customer1)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_analyzed.id})
        data = {"price_usd": "99.00", "estimated_lead_time_days": 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    # --- Quote Listing Tests (/api/designs/{design_id}/quotes/) ---
    def test_design_owner_list_quotes(self):
        self._login(self.customer1)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_analyzed.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(uuid.UUID(response.data[0]['id']), self.quote_mf1_design_c1.id)

    def test_quoting_manufacturer_list_their_quote(self):
        self._login(self.manufacturer1)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_analyzed.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(uuid.UUID(response.data[0]['id']), self.quote_mf1_design_c1.id)

    def test_other_manufacturer_list_empty_for_design(self):
        self._login(self.manufacturer2)
        url = reverse('design_quote_list_create', kwargs={'design_id': self.design_c1_analyzed.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # --- Quote Detail Tests (/api/quotes/{quote_id}/) ---
    def test_design_owner_retrieve_quote_detail(self):
        self._login(self.customer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(uuid.UUID(response.data['id']), self.quote_mf1_design_c1.id)

    def test_quoting_manufacturer_retrieve_quote_detail(self):
        self._login(self.manufacturer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(uuid.UUID(response.data['id']), self.quote_mf1_design_c1.id)

    def test_other_user_cannot_retrieve_quote_detail(self):
        self._login(self.manufacturer2)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    # --- Quote Update Tests (/api/quotes/{quote_id}/) ---
    def test_customer_accept_quote(self):
        self._login(self.customer1)

        # Ensure the quote to be accepted is initially PENDING
        self.quote_mf1_design_c1.status = QuoteStatus.PENDING
        self.quote_mf1_design_c1.save()

        # Create another pending quote for the same design by another manufacturer
        quote_mf2_design_c1 = Quote.objects.create(
            design=self.design_c1_analyzed, manufacturer=self.manufacturer2,
            price_usd="180.00", estimated_lead_time_days=12, status=QuoteStatus.PENDING
        )

        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        data = {"status": QuoteStatus.ACCEPTED.value}

        # Make the API call to accept the quote
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.quote_mf1_design_c1.refresh_from_db()
        self.assertEqual(self.quote_mf1_design_c1.status, QuoteStatus.ACCEPTED)


        # Verify Order creation
        from orders.models import Order, OrderStatus as OrderModelStatus # Import locally for test
        self.assertTrue(Order.objects.filter(accepted_quote=self.quote_mf1_design_c1).exists())
        order = Order.objects.get(accepted_quote=self.quote_mf1_design_c1)
        self.assertEqual(order.design, self.quote_mf1_design_c1.design)
        self.assertEqual(order.customer, self.customer1)
        self.assertEqual(order.manufacturer, self.manufacturer1)
        self.assertEqual(order.order_total_price_usd, self.quote_mf1_design_c1.price_usd)
        self.assertEqual(order.status, OrderModelStatus.PENDING_PAYMENT) # Default status for new order

        # Verify estimated delivery date calculation (approximate)
        from django.utils import timezone
        from datetime import timedelta
        expected_delivery_date = (order.created_at or timezone.now()).date() + \
                                 timedelta(days=self.quote_mf1_design_c1.estimated_lead_time_days)
        self.assertEqual(order.estimated_delivery_date, expected_delivery_date)

        # Verify Design status update
        self.design_c1_analyzed.refresh_from_db()
        self.assertEqual(self.design_c1_analyzed.status, DesignModelStatus.ORDERED)

        # Verify other quotes for the same design are rejected
        # Note: quote_mf2_design_c1 was created *before* the patch call that accepted self.quote_mf1_design_c1.
        # So, its status should have been updated by the view logic.
        quote_mf2_design_c1.refresh_from_db()
        self.assertEqual(quote_mf2_design_c1.status, QuoteStatus.REJECTED)


    def test_customer_reject_quote(self):
        self._login(self.customer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        data = {"status": QuoteStatus.REJECTED.value}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.quote_mf1_design_c1.refresh_from_db()
        self.assertEqual(self.quote_mf1_design_c1.status, QuoteStatus.REJECTED)

    def test_customer_invalid_status_update(self):
        self._login(self.customer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        data = {"status": QuoteStatus.EXPIRED.value}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_manufacturer_update_pending_quote_details(self):
        self._login(self.manufacturer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        data = {"price_usd": "160.00", "notes": "Updated notes for pending quote"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.quote_mf1_design_c1.refresh_from_db()
        self.assertEqual(float(self.quote_mf1_design_c1.price_usd), 160.00)
        self.assertEqual(self.quote_mf1_design_c1.notes, data['notes'])

    def test_manufacturer_cannot_accept_own_quote(self):
        self._login(self.manufacturer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        data = {"status": QuoteStatus.ACCEPTED.value}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    # --- Quote Deletion Tests (/api/quotes/{quote_id}/) ---
    def test_manufacturer_delete_pending_quote(self):
        self._login(self.manufacturer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quote.objects.filter(id=self.quote_mf1_design_c1.id).exists())

    def test_manufacturer_cannot_delete_accepted_quote(self):
        self.quote_mf1_design_c1.status = QuoteStatus.ACCEPTED
        self.quote_mf1_design_c1.save()
        self._login(self.manufacturer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_customer_cannot_delete_quote(self):
        self._login(self.customer1)
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_admin_can_delete_any_quote(self):
        self._login(self.admin_user)
        self.quote_mf1_design_c1.status = QuoteStatus.ACCEPTED
        self.quote_mf1_design_c1.save()
        url = reverse('quote_detail', kwargs={'id': self.quote_mf1_design_c1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quote.objects.filter(id=self.quote_mf1_design_c1.id).exists())
