from rest_framework import generics, permissions, status, serializers, exceptions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Quote, QuoteStatus
from .serializers import QuoteSerializer
from designs.models import Design, DesignStatus as DesignModelStatus
from accounts.models import UserRole

# --- Custom Permissions for Quotes ---

class IsQuoteOwnerOrDesignOwnerOrAdmin(permissions.BasePermission):
    """
    General permission for viewing/deleting a quote:
    - Manufacturer who created the quote (quote owner).
    - Customer who owns the design associated with the quote.
    - Admin users.
    """
    def has_object_permission(self, request, view, obj): # obj is a Quote instance
        if request.user.is_staff:
            return True
        return obj.manufacturer == request.user or obj.design.customer == request.user

class CanCreateQuoteForDesign(permissions.BasePermission):
    """
    Permission for creating a quote for a specific design:
    - User must be an authenticated manufacturer.
    - User cannot be the owner of the design they are quoting.
    - Design must be in a state that accepts quotes (e.g., ANALYSIS_COMPLETE).
    """
    message = "You do not have permission to create a quote for this design."

    def has_permission(self, request, view): # view-level permission
        if not (request.user and request.user.is_authenticated and request.user.role == UserRole.MANUFACTURER):
            self.message = "Only authenticated manufacturers can create quotes."
            return False

        design_id = view.kwargs.get('design_id')
        if not design_id: # Should not happen if URL is correctly configured
            self.message = "Design ID not provided in URL."
            return False

        try:
            design = Design.objects.get(pk=design_id)
        except Design.DoesNotExist:
            self.message = "Design not found." # get_object_or_404 will handle this in view if preferred
            return False

        if design.customer == request.user:
            self.message = "Manufacturers cannot quote their own designs."
            return False

        # Check if design status allows quoting
        if design.status != DesignModelStatus.ANALYSIS_COMPLETE:
            self.message = (
                f"Design must be in '{DesignModelStatus.ANALYSIS_COMPLETE.label}' status to receive quotes. "
                f"Current status: {design.get_status_display()}."
            )
            return False

        return True

class CanUpdateQuote(permissions.BasePermission):
    """
    Permission for updating a quote (e.g. its status):
    - Customer (design owner) can accept/reject PENDING quotes.
    - Manufacturer (quote creator) can potentially modify PENDING quotes (e.g. price, notes, not status typically)
      or expire/withdraw them if business logic allows.
    - Admin users.
    """
    message = "You do not have permission to update this quote or perform this status change."

    def has_object_permission(self, request, view, obj): # obj is a Quote instance
        if request.user.is_staff:
            return True

        # Who is making the request?
        is_design_owner = (obj.design.customer == request.user)
        is_quote_creator = (obj.manufacturer == request.user)

        if not (is_design_owner or is_quote_creator):
            return False # Not involved at all

        # If only status is being updated
        if 'status' in request.data and len(request.data) == 1:
            new_status = request.data.get('status')
            if is_design_owner:
                if obj.status == QuoteStatus.PENDING and new_status in [QuoteStatus.ACCEPTED, QuoteStatus.REJECTED]:
                    return True
                self.message = f"Customer can only change status from Pending to Accepted/Rejected. Invalid transition from '{obj.status}' to '{new_status}'."
                return False
            elif is_quote_creator:
                # Manufacturers typically don't change status to accepted/rejected.
                # They might be allowed to change to EXPIRED or withdraw (custom status).
                if obj.status == QuoteStatus.PENDING and new_status == QuoteStatus.EXPIRED: # Example
                    return True
                self.message = f"Manufacturer cannot make this status transition from '{obj.status}' to '{new_status}'."
                return False
        elif is_quote_creator and obj.status == QuoteStatus.PENDING:
            # Allow manufacturer to update other fields (price, notes, lead_time) if quote is PENDING
            # but not status itself, unless to EXPIRED as handled above.
            if 'status' in request.data and request.data['status'] != obj.status: # Trying to change status to non-EXPIRED
                 self.message = "Manufacturer can only update details of a PENDING quote, or mark it EXPIRED."
                 return False
            return True # Allow update of other fields by manufacturer if PENDING

        # If not just a status update, and not a manufacturer updating a PENDING quote
        self.message = "You cannot update this quote in its current state or with the provided data."
        return False

# --- API Views for Quotes ---

class QuoteListCreateView(generics.ListCreateAPIView):
    """
    GET /api/designs/{design_id}/quotes/ - List quotes for a specific design.
    POST /api/designs/{design_id}/quotes/ - Create a quote for a specific design.
    """
    serializer_class = QuoteSerializer
    # permission_classes = [permissions.IsAuthenticated] # Base permission

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), CanCreateQuoteForDesign()]
        return [permissions.IsAuthenticated()] # For GET, queryset filtering handles visibility

    def get_queryset(self):
        design_id = self.kwargs.get('design_id')
        # Ensure design exists, or let it 404 if not found (handled by get_object_or_404 in dispatch)
        design = get_object_or_404(Design, pk=design_id)
        user = self.request.user

        if user.is_staff: # Admin sees all quotes for the design
            return Quote.objects.filter(design=design).select_related('manufacturer', 'design')
        if design.customer == user: # Design owner sees all quotes for their design
            return Quote.objects.filter(design=design).select_related('manufacturer', 'design')
        if user.role == UserRole.MANUFACTURER: # Manufacturer sees only their quotes for this design
            return Quote.objects.filter(design=design, manufacturer=user).select_related('manufacturer', 'design')

        return Quote.objects.none() # Other users see none

    def perform_create(self, serializer):
        design_id = self.kwargs.get('design_id')
        design = get_object_or_404(Design, pk=design_id) # Already validated by CanCreateQuoteForDesign

        # Prevent duplicate quotes by the same manufacturer for the same design
        if Quote.objects.filter(design=design, manufacturer=self.request.user).exists():
            raise serializers.ValidationError( # DRF validation error for 400 response
                {"detail": "You have already submitted a quote for this design."}
            )
        serializer.save(design=design, manufacturer=self.request.user)


class QuoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/quotes/{quote_id}/ - Retrieve a specific quote.
    PUT/PATCH /api/quotes/{quote_id}/ - Update a quote.
    DELETE /api/quotes/{quote_id}/ - Delete a quote.
    """
    queryset = Quote.objects.select_related('design', 'manufacturer', 'design__customer').all()
    serializer_class = QuoteSerializer
    lookup_field = 'id'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), CanUpdateQuote()]
        # For GET/DELETE:
        return [permissions.IsAuthenticated(), IsQuoteOwnerOrDesignOwnerOrAdmin()]

    def perform_destroy(self, instance):
        # Only manufacturer can delete their PENDING quotes (or admin)
        if not (self.request.user.is_staff or
                (instance.manufacturer == self.request.user and instance.status == QuoteStatus.PENDING)):
            raise exceptions.PermissionDenied( # Corrected here
                "You can only delete PENDING quotes that you created."
            )
        super().perform_destroy(instance)

    def perform_update(self, serializer):
        logger = __import__('logging').getLogger(__name__) # Define logger at the start of the method
        quote_instance = serializer.instance
        original_status = quote_instance.status
        new_status = serializer.validated_data.get('status', original_status)

        # Save the quote update
        updated_quote = serializer.save()

        # If status changed to ACCEPTED, create an Order
        if original_status != QuoteStatus.ACCEPTED and new_status == QuoteStatus.ACCEPTED:
            from orders.models import Order # Avoid circular import at top level
            from django.db import transaction

            try:
                with transaction.atomic():
                    # Ensure no duplicate order for this quote
                    if hasattr(updated_quote, 'order_created_from'):
                        # This means an order already exists, which ideally shouldn't happen if status transitions are correct
                        # Or if this endpoint can be called multiple times to "re-accept".
                        # For now, assume we just log and don't create a new one.
                        # If re-accepting should update the order, that's different logic.
                        logger = __import__('logging').getLogger(__name__)
                        logger.warning(f"Quote {updated_quote.id} re-accepted, but order already exists: {updated_quote.order_created_from.id}")
                        return

                    # Create the order
                    order = Order.objects.create(
                        design=updated_quote.design,
                        accepted_quote=updated_quote,
                        customer=updated_quote.design.customer,
                        manufacturer=updated_quote.manufacturer,
                        order_total_price_usd=updated_quote.price_usd,
                        # Initial status for order, e.g., PENDING_PAYMENT
                        # from orders.models import OrderStatus as OS
                        # status=OS.PENDING_PAYMENT
                        # (OrderStatus will be imported in orders.models, direct import here for clarity)
                    )
                    # Calculate and set estimated delivery date
                    order.calculate_and_set_estimated_delivery(
                        quote_lead_time_days=updated_quote.estimated_lead_time_days
                    )
                    order.save() # Save again if calculate_and_set_estimated_delivery doesn't save

                    # Optionally, update related design status if applicable
                    # For example, if the design should now be considered 'Ordered'
                    if updated_quote.design.status != DesignModelStatus.ORDERED:
                         updated_quote.design.status = DesignModelStatus.ORDERED
                         updated_quote.design.save(update_fields=['status', 'updated_at'])

                    # Reject other pending quotes for the same design
                    design_pk = updated_quote.design.pk
                    other_pending_quotes = Quote.objects.filter(
                        design_id=design_pk, # Explicitly use design_id
                        status=QuoteStatus.PENDING
                    ).exclude(id=updated_quote.id)

                    logger.debug(f"Found {other_pending_quotes.count()} other pending quotes to reject for design {design_pk}.")
                    for q in other_pending_quotes:
                        logger.debug(f"Rejecting quote {q.id}")
                        q.status = QuoteStatus.REJECTED
                        q.save(update_fields=['status', 'updated_at'])

            except Exception as e:
                # Log the error, and potentially revert quote status if order creation is critical
                # For now, the quote status is already saved as ACCEPTED.
                # A more robust solution might use a post_save signal on Quote for order creation.
                logger = __import__('logging').getLogger(__name__)
                logger.error(f"Error creating order for accepted quote {updated_quote.id}: {e}")
                # serializer.instance.status = original_status # Revert status? Complex interaction.
                # serializer.instance.save()
                # raise serializers.ValidationError({"detail": "Order creation failed after quote acceptance."})
                # For now, let the quote remain accepted, but log the order creation failure.
                # The client might not be aware of this partial failure.
                pass # Or re-raise a specific error if this should fail the whole update.
