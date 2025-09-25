from rest_framework import generics, permissions
from .models import Order
from .serializers import OrderSerializer
from accounts.models import UserRole # To check user roles

# --- Custom Permissions for Orders ---

class IsOrderParticipantOrAdmin(permissions.BasePermission):
    """
    Permission to ensure only the customer who placed the order,
    the manufacturer fulfilling it, or an admin can view/access the order.
    """
    def has_object_permission(self, request, view, obj): # obj is an Order instance
        if request.user and request.user.is_authenticated: # Ensure user is authenticated
            if request.user.is_staff:
                return True
            return obj.customer == request.user or obj.manufacturer == request.user
        return False

# --- API Views for Orders ---

class OrderListView(generics.ListAPIView):
    """
    GET /api/orders/
    - Customers see orders they placed.
    - Manufacturers see orders they received.
    - Admins see all orders.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # select_related is used to optimize queries by fetching related objects in a single DB hit.
        base_queryset = Order.objects.select_related(
            'design',
            'accepted_quote',
            'customer', # User object for customer
            'manufacturer' # User object for manufacturer
        )

        if user.is_staff:
            return base_queryset.all()
        elif user.role == UserRole.CUSTOMER:
            return base_queryset.filter(customer=user)
        elif user.role == UserRole.MANUFACTURER:
            return base_queryset.filter(manufacturer=user)

        return Order.objects.none() # Should ideally not be reached if user is authenticated


class OrderDetailView(generics.RetrieveUpdateAPIView): # Changed to allow Update (PATCH/PUT)
    """
    GET /api/orders/{order_id}/ - Retrieve a specific order.
    PATCH /api/orders/{order_id}/ - Partially update an order (e.g., status, tracking).
    PUT /api/orders/{order_id}/ - Update an order (less common for partial updates).
    - Accessible by the customer who placed it, the manufacturer fulfilling it, or an admin,
      with specific field update permissions handled by CanUpdateSpecificOrderFieldsPermission.
    """
    queryset = Order.objects.select_related(
        'design',
        'accepted_quote',
        'customer',
        'manufacturer'
    ).all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderParticipantOrAdmin] # Base permission for GET
    lookup_field = 'id' # Order model PK is 'id' (UUID)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        For PUT/PATCH, use a more specific permission class.
        """
        if self.request.method in ['PUT', 'PATCH']:
            return [permissions.IsAuthenticated(), CanUpdateSpecificOrderFieldsPermission()]
        return super().get_permissions()


class CanUpdateSpecificOrderFieldsPermission(permissions.BasePermission):
    """
    Custom permission to control updates to specific Order fields based on user role.
    - Manufacturer: Can update status (defined transitions), tracking_number, shipping_carrier, actual_ship_date.
    - Customer: Can update status to CANCELLED_BY_CUSTOMER (if order is cancelable).
    - Admin: Can update these fields.
    """
    message = "You do not have permission to update this field or make this status transition."

    def has_object_permission(self, request, view, obj): # obj is an Order instance
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff:
            return True

        # Check if the user is either the customer or the manufacturer for this order
        is_customer = (obj.customer == request.user)
        is_manufacturer = (obj.manufacturer == request.user)

        if not (is_customer or is_manufacturer):
            return False # User is not related to the order

        # What fields are being updated?
        updated_fields = request.data.keys()
        allowed_fields_manufacturer = {'status', 'tracking_number', 'shipping_carrier', 'actual_ship_date', 'cancellation_reason'}
        allowed_fields_customer = {'status', 'shipping_address', 'cancellation_reason'} # Customer might update shipping if not shipped

        # Check if trying to update forbidden fields
        if is_manufacturer:
            for field in updated_fields:
                if field not in allowed_fields_manufacturer:
                    self.message = f"Manufacturer cannot update field: {field}."
                    return False
        elif is_customer:
            for field in updated_fields:
                if field not in allowed_fields_customer:
                    self.message = f"Customer cannot update field: {field}."
                    return False

        # Status transition validation (moved from serializer for more context here)
        if 'status' in updated_fields:
            current_status = obj.status
            new_status = request.data.get('status')

            if is_manufacturer:
                allowed_transitions = {
                    OrderStatus.PENDING_MANUFACTURER_CONFIRMATION: [OrderStatus.PROCESSING, OrderStatus.CANCELLED_BY_MANUFACTURER],
                    OrderStatus.PROCESSING: [OrderStatus.IN_PRODUCTION, OrderStatus.CANCELLED_BY_MANUFACTURER],
                    OrderStatus.IN_PRODUCTION: [OrderStatus.SHIPPED],
                    OrderStatus.SHIPPED: [OrderStatus.COMPLETED],
                }
                if current_status not in allowed_transitions or new_status not in allowed_transitions[current_status]:
                    self.message = f"Manufacturer: Invalid status transition from '{current_status}' to '{new_status}'."
                    return False
                # If setting to SHIPPED, ensure tracking info might be expected (handled by serializer update method for now)

            elif is_customer:
                # Customer can only cancel if order is in a pre-production state
                cancelable_statuses = [
                    OrderStatus.PENDING_MANUFACTURER_CONFIRMATION,
                    OrderStatus.PENDING_PAYMENT,
                    OrderStatus.PROCESSING
                ]
                if new_status == OrderStatus.CANCELLED_BY_CUSTOMER and current_status in cancelable_statuses:
                    if not request.data.get('cancellation_reason'): # Require reason for customer cancellation
                        self.message = "Please provide a reason for cancelling the order."
                        return False
                    return True
                elif new_status == OrderStatus.CANCELLED_BY_CUSTOMER and current_status not in cancelable_statuses:
                     self.message = f"Order cannot be cancelled by customer in its current status: '{current_status}'."
                     return False
                else: # Customer trying other status changes
                    self.message = "Customer can only cancel orders in specific states or update shipping address."
                    return False

        # Customer updating shipping address
        if is_customer and 'shipping_address' in updated_fields:
            # Allow customer to update shipping address if order is not too far in progress
            if obj.status in [OrderStatus.SHIPPED, OrderStatus.IN_PRODUCTION, OrderStatus.COMPLETED, OrderStatus.CANCELLED_BY_MANUFACTURER]:
                self.message = f"Shipping address cannot be updated when order status is '{obj.status}'."
                return False

        return True # All checks passed for the role and attempted field updates


from rest_framework.views import APIView
from .models import OrderStatus # Ensure OrderStatus is available
from django.shortcuts import get_object_or_404
from django.db import transaction

class OrderPaymentView(APIView):
    """
    POST /api/orders/{order_id}/process-payment/
    Simulates processing a payment for an order.
    """
    permission_classes = [permissions.IsAuthenticated, IsOrderParticipantOrAdmin] # Only customer of order or admin

    def post(self, request, id, *args, **kwargs): # 'id' is order_id
        order = get_object_or_404(Order, id=id)

        # Manually check if the user is the customer of this order for this specific action
        if order.customer != request.user and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to process payment for this order."},
                status=status.HTTP_403_FORBIDDEN
            )

        if order.status != OrderStatus.PENDING_PAYMENT:
            return Response(
                {"error": f"Order is not pending payment. Current status: {order.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Placeholder: Simulate payment success/failure
        # In a real app, this would involve integrating with a payment gateway (Stripe, PayPal, etc.)
        # For simulation, let's assume a dummy token "valid_dummy_token" means success.
        payment_token = request.data.get("payment_token")
        payment_successful = (payment_token == "valid_dummy_token")

        with transaction.atomic():
            if payment_successful:
                # Assuming the next step after payment is manufacturer confirmation or processing
                # If PENDING_MANUFACTURER_CONFIRMATION is used after payment, change to that.
                # If payment happens after manufacturer confirmation, then PROCESSING is fine.
                # Current flow: Quote Accepted -> Order (PENDING_MANUF_CONFIRM) -> Manuf Confirms (-> PROCESSING or PENDING_PAYMENT)
                # Let's adjust the flow: Order created with PENDING_PAYMENT after quote acceptance.
                # Manuf. confirmation could be an implicit part of them not cancelling.
                # So, successful payment moves to PROCESSING.
                order.status = OrderStatus.PROCESSING
                order.save(update_fields=['status', 'updated_at'])
                # Potentially trigger notifications or next steps for manufacturer
                return Response({"message": "Payment successful. Order is now processing."}, status=status.HTTP_200_OK)
            else:
                order.status = OrderStatus.PAYMENT_FAILED
                order.save(update_fields=['status', 'updated_at'])
                return Response({"error": "Payment failed. Please try again or use a different payment method."}, status=status.HTTP_400_BAD_REQUEST)
