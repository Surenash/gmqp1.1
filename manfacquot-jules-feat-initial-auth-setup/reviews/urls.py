from django.urls import path
from .views import ReviewListCreateView, ReviewDetailView

# Base for these URLs will likely be /api/
# URLs related to reviews.
# Similar to quotes, review creation is often nested.
# e.g., /api/manufacturers/{manufacturer_id}/reviews/ (for list/create)
# and /api/reviews/{review_id}/ (for detail/update/delete)

urlpatterns = [
    # Specific review operations by review ID
    path('<uuid:id>', ReviewDetailView.as_view(), name='review_detail'),
]

# For URLs to be included by other apps (like accounts/manufacturers for listing/creating reviews for a manufacturer)
manufacturer_specific_review_urlpatterns = [
    path('', ReviewListCreateView.as_view(), name='manufacturer_review_list_create'),
]
