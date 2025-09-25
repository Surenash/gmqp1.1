import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, UserRole
from .models import Review

class ReviewAPITests(APITestCase):

    def setUp(self):
        self.customer1 = User.objects.create_user(
            email="reviewer_customer1@example.com", password="Password123!",
            company_name="Reviewer One Corp", role=UserRole.CUSTOMER
        )
        self.customer2 = User.objects.create_user(
            email="reviewer_customer2@example.com", password="Password123!",
            company_name="Reviewer Two Inc", role=UserRole.CUSTOMER
        )
        self.manufacturer1 = User.objects.create_user(
            email="reviewed_mf1@example.com", password="Password123!",
            company_name="Reviewed Manuf One", role=UserRole.MANUFACTURER
        )
        # Ensure Manufacturer profile exists if any related logic depends on it
        # from accounts.models import Manufacturer as ManufacturerProfile
        # ManufacturerProfile.objects.get_or_create(user=self.manufacturer1)

        self.manufacturer2 = User.objects.create_user(
            email="reviewed_mf2@example.com", password="Password123!",
            company_name="Reviewed Manuf Two", role=UserRole.MANUFACTURER
        )
        # ManufacturerProfile.objects.get_or_create(user=self.manufacturer2)

        self.admin_user = User.objects.create_superuser(
            email="admin_reviews@example.com", password="Password123!", company_name="AdminReviewCo"
        )

        self.review_c1_mf1 = Review.objects.create(
            customer=self.customer1,
            manufacturer=self.manufacturer1,
            rating=5,
            comment="Excellent service!"
            # order_id=None by default
        )
        self.review_c2_mf1_order = Review.objects.create(
            customer=self.customer2,
            manufacturer=self.manufacturer1, # mf1 reviewed by two customers
            rating=4,
            comment="Good, but a bit slow.",
            order_id=uuid.uuid4() # With an order_id
        )

    def _login(self, user_obj):
        self.client.force_authenticate(user=user_obj)

    # --- Review Creation Tests (/api/manufacturers/{manufacturer_id}/reviews/) ---
    def test_customer_create_review_success(self):
        self._login(self.customer1)
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer2.id})
        data = {"rating": 3, "comment": "Average experience.", "order_id": str(uuid.uuid4())}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Review.objects.count(), 3)
        new_review = Review.objects.get(id=response.data['id'])
        self.assertEqual(new_review.customer, self.customer1)
        self.assertEqual(new_review.manufacturer, self.manufacturer2)
        self.assertEqual(new_review.rating, 3)

    def test_customer_cannot_review_same_manufacturer_twice_no_orderid(self):
        self._login(self.customer1)
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer1.id})
        data = {"rating": 2, "comment": "Trying to review again (no order_id)."}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        # Message comes from serializer's validate method or view's perform_create check
        self.assertTrue(
            "already submitted a review" in response.data.get("detail", "") or \
            any("already submitted a review" in e for e in response.data.get("non_field_errors", [])) or \
            any("already submitted a review" in e for e in response.data.get("__all__", []))
        )


    def test_customer_can_review_same_manufacturer_with_different_orderid(self):
        self._login(self.customer1)
        # self.review_c1_mf1 was created without order_id in setUp for manufacturer1
        # Now, create a new review for manufacturer1 WITH an order_id
        order_id_for_new_review = uuid.uuid4()
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer1.id})
        data = {"rating": 4, "comment": "Review for a specific order.", "order_id": str(order_id_for_new_review)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(Review.objects.filter(customer=self.customer1, manufacturer=self.manufacturer1, order_id=order_id_for_new_review).exists())

    def test_customer_cannot_review_same_order_twice(self):
        self._login(self.customer2) # customer2 made review_c2_mf1_order in setUp
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer1.id})
        data = {
            "rating": 3, "comment": "Trying to review same order again.",
            "order_id": str(self.review_c2_mf1_order.order_id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertTrue(
            "already submitted a review" in response.data.get("detail", "") or \
            any("already submitted a review" in e for e in response.data.get("non_field_errors", [])) or \
            any("already submitted a review" in e for e in response.data.get("__all__", []))
        )


    def test_create_review_invalid_rating(self):
        self._login(self.customer1)
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer2.id})
        data_low = {"rating": 0, "comment": "Rating too low."}
        response_low = self.client.post(url, data_low, format='json')
        self.assertEqual(response_low.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rating", response_low.data)

        data_high = {"rating": 6, "comment": "Rating too high."}
        response_high = self.client.post(url, data_high, format='json')
        self.assertEqual(response_high.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rating", response_high.data)

    def test_manufacturer_cannot_create_review(self):
        self._login(self.manufacturer1)
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer2.id})
        data = {"rating": 5, "comment": "MF reviewing MF"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    # --- Review Listing Tests (/api/manufacturers/{manufacturer_id}/reviews/) ---
    def test_list_reviews_for_manufacturer_public(self):
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        review_ids_in_response = {uuid.UUID(item['id']) for item in response.data}
        self.assertIn(self.review_c1_mf1.id, review_ids_in_response)
        self.assertIn(self.review_c2_mf1_order.id, review_ids_in_response)

    def test_list_reviews_for_manufacturer_with_no_reviews(self):
        url = reverse('manufacturer_review_list_create', kwargs={'manufacturer_id': self.manufacturer2.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    # --- Review Detail Tests (/api/reviews/{review_id}/) ---
    def test_retrieve_review_detail_public(self):
        url = reverse('review_detail', kwargs={'id': self.review_c1_mf1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(uuid.UUID(response.data['id']), self.review_c1_mf1.id)
        self.assertEqual(response.data['comment'], self.review_c1_mf1.comment)

    # --- Review Update Tests (/api/reviews/{review_id}/) ---
    def test_review_owner_can_update_review(self):
        self._login(self.customer1)
        url = reverse('review_detail', kwargs={'id': self.review_c1_mf1.id})
        update_data = {"rating": 4, "comment": "Updated comment."}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.review_c1_mf1.refresh_from_db()
        self.assertEqual(self.review_c1_mf1.rating, 4)
        self.assertEqual(self.review_c1_mf1.comment, "Updated comment.")

    def test_non_owner_cannot_update_review(self):
        self._login(self.customer2)
        url = reverse('review_detail', kwargs={'id': self.review_c1_mf1.id})
        update_data = {"comment": "Attempted update by non-owner."}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    def test_manufacturer_cannot_update_review_about_them(self):
        self._login(self.manufacturer1)
        url = reverse('review_detail', kwargs={'id': self.review_c1_mf1.id})
        update_data = {"comment": "Manufacturer trying to edit review."}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

    # --- Review Deletion Tests (/api/reviews/{review_id}/) ---
    def test_review_owner_can_delete_review(self):
        self._login(self.customer1)
        review_id_to_delete = self.review_c1_mf1.id
        url = reverse('review_detail', kwargs={'id': review_id_to_delete})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review_id_to_delete).exists())

    def test_non_owner_cannot_delete_review(self):
        self._login(self.customer2)
        url = reverse('review_detail', kwargs={'id': self.review_c1_mf1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Review.objects.filter(id=self.review_c1_mf1.id).exists())

    def test_admin_can_delete_any_review(self):
        self._login(self.admin_user)
        review_id_to_delete = self.review_c1_mf1.id
        url = reverse('review_detail', kwargs={'id': review_id_to_delete})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review_id_to_delete).exists())
