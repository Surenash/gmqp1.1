from rest_framework import generics, permissions, serializers
from django.shortcuts import get_object_or_404
from .models import Review
from .serializers import ReviewSerializer
from accounts.models import User, UserRole # Assuming UserRole is here

# --- Custom Permissions for Reviews ---

class CanCreateReviewForManufacturer(permissions.BasePermission):
    """
    Permission for creating a review for a specific manufacturer:
    - User must be an authenticated customer.
    - User cannot review themselves (implicitly handled by role checks if manufacturer_id is a different user).
    - (Future enhancement: Check if customer has a completed order with this manufacturer).
    """
    message = "You do not have permission to create this review."

    def has_permission(self, request, view): # View-level permission
        if not (request.user and request.user.is_authenticated and request.user.role == UserRole.CUSTOMER):
            self.message = "Only authenticated customers can submit reviews."
            return False

        manufacturer_id_from_url = view.kwargs.get('manufacturer_id')
        if not manufacturer_id_from_url: # Should not happen if URL is correctly configured
            self.message = "Manufacturer ID not provided in URL."
            return False

        try:
            # Ensure the manufacturer_id from URL corresponds to an actual manufacturer
            manufacturer_user = User.objects.get(pk=manufacturer_id_from_url, role=UserRole.MANUFACTURER)
        except User.DoesNotExist:
            self.message = "Manufacturer to be reviewed not found or is not a valid manufacturer."
            return False

        # A customer cannot be a manufacturer, so request.user != manufacturer_user is implicitly true.
        # If a user could have multiple roles, this check would be more important:
        # if request.user.id == manufacturer_user.id:
        # self.message = "Users cannot review themselves."
        # return False
        return True

class IsReviewOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of a review to edit/delete it.
    Read is allowed for anyone (if view is IsAuthenticatedOrReadOnly).
    Admin users have full access implicitly via is_staff checks in views or higher permissions.
    """
    def has_object_permission(self, request, view, obj): # obj is a Review instance
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the review or staff.
        return request.user.is_staff or obj.customer == request.user


# --- API Views for Reviews ---

class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET /api/manufacturers/{manufacturer_id}/reviews/ - List reviews for a specific manufacturer. (Public)
    POST /api/manufacturers/{manufacturer_id}/reviews/ - Create a review for a specific manufacturer (by a customer).
    """
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            # For POST, user must be authenticated customer, and can create review for this manufacturer
            return [permissions.IsAuthenticated(), CanCreateReviewForManufacturer()]
        # For GET (list), reviews are public
        return [permissions.AllowAny()]

    def get_queryset(self):
        manufacturer_id = self.kwargs.get('manufacturer_id')
        # Ensure manufacturer exists and is valid (role check), or let it 404
        manufacturer = get_object_or_404(User, pk=manufacturer_id, role=UserRole.MANUFACTURER)
        return Review.objects.filter(manufacturer=manufacturer).select_related('customer', 'manufacturer').order_by('-created_at')

    def perform_create(self, serializer):
        manufacturer_id = self.kwargs.get('manufacturer_id')
        manufacturer = get_object_or_404(User, pk=manufacturer_id, role=UserRole.MANUFACTURER) # Already validated by permission

        # Prevent duplicate reviews (this logic is also in serializer, good for defense in depth)
        order_id = serializer.validated_data.get('order_id')

        # Check for existing review by this customer for this manufacturer (and optionally order)
        # This is an example, the exact definition of "duplicate" might vary.
        # The serializer's validate method already has a similar check.
        # If it's preferred to keep this logic solely in serializer, this block can be simplified/removed.
        existing_review_query = Review.objects.filter(
            customer=self.request.user,
            manufacturer=manufacturer
        )
        if order_id:
            existing_review_query = existing_review_query.filter(order_id=order_id)
        else: # If new review has no order_id, check against existing reviews with no order_id
            existing_review_query = existing_review_query.filter(order_id__isnull=True)

        if existing_review_query.exists():
            raise serializers.ValidationError(
                {"detail": "You have already submitted a review for this manufacturer " +
                           ("for this order." if order_id else "(general review).")}
            )

        serializer.save(customer=self.request.user, manufacturer=manufacturer)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/reviews/{review_id}/ - Retrieve a specific review. (Public)
    PUT/PATCH /api/reviews/{review_id}/ - Update a review (by owner or admin).
    DELETE /api/reviews/{review_id}/ - Delete a review (by owner or admin).
    """
    queryset = Review.objects.select_related('customer', 'manufacturer').all()
    serializer_class = ReviewSerializer
    permission_classes = [IsReviewOwnerOrReadOnly] # Handles both read (any) and write (owner/admin)
    lookup_field = 'id' # Review model PK is 'id'

    # perform_update and perform_destroy will respect IsReviewOwnerOrReadOnly.
    # No specific overrides needed unless further logic is required (e.g. cannot edit after X days).
