from django.urls import path, include # Added include
from .views import UserRegistrationView, CustomTokenObtainPairView, CurrentUserView
from . import views # Import views to access Manufacturer views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # POST /api/auth/register (from spec)
    path('register', UserRegistrationView.as_view(), name='user_register'),

    # POST /api/auth/token (from spec)
    path('token', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # POST /api/auth/token/refresh (standard for JWT refresh)
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    # GET /api/auth/me (example protected route to get current user)
    path('me', CurrentUserView.as_view(), name='current_user'),
]

# Import the specific list from reviews.urls first
from reviews.urls import manufacturer_specific_review_urlpatterns as manufacturer_specific_review_urlpatterns_from_reviews_app

# Separate list for manufacturer specific URLs, to be included with a different prefix
# if these were in a separate 'manufacturers' app, this list would be in manufacturers/urls.py
manufacturer_urlpatterns = [
    path('', views.ManufacturerListView.as_view(), name='manufacturer_list'), # GET /api/manufacturers/
    path('profile', views.ManufacturerProfileUpdateView.as_view(), name='manufacturer_profile_update'), # GET, PUT /api/manufacturers/profile/
    path('<uuid:user_id>', views.ManufacturerDetailView.as_view(), name='manufacturer_detail'), # GET /api/manufacturers/<user_id_uuid>/

    # Nested reviews for a manufacturer: /api/manufacturers/<uuid:manufacturer_id>/reviews/
    # Note: user_id in ManufacturerDetailView and manufacturer_id here both refer to User ID.
    path('<uuid:manufacturer_id>/reviews/', include(manufacturer_specific_review_urlpatterns_from_reviews_app)), # Use the imported list
]
