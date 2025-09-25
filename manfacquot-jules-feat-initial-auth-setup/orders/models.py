import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # For calculating estimated_delivery_date
from datetime import timedelta # For calculating estimated_delivery_date


# It's better to import from the app's models.py directly if possible,
# but be mindful of circular dependencies.
# from designs.models import Design # Causes circular if Design imports Order for a related_name
# from quotes.models import Quote   # Causes circular if Quote imports Order for a related_name
from accounts.models import UserRole # To limit choices for customer/manufacturer

class OrderStatus(models.TextChoices):
    PENDING_MANUFACTURER_CONFIRMATION = 'pending_manuf_confirm', _('Pending Manufacturer Confirmation')
    PENDING_PAYMENT = 'pending_payment', _('Pending Payment')
    PROCESSING = 'processing', _('Processing') # e.g. payment confirmed, manuf accepted & confirmed
    PAYMENT_FAILED = 'payment_failed', _('Payment Failed') # New status for payment failure
    IN_PRODUCTION = 'in_production', _('In Production')
    SHIPPED = 'shipped', _('Shipped')
    COMPLETED = 'completed', _('Completed')
    CANCELLED_BY_CUSTOMER = 'cancelled_customer', _('Cancelled by Customer')
    CANCELLED_BY_MANUFACTURER = 'cancelled_manufacturer', _('Cancelled by Manufacturer')
    # Consider: PENDING_MANUFACTURER_CONFIRMATION, DISPUTED, REFUNDED

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    design = models.ForeignKey(
        'designs.Design', # Use string reference to avoid circular import
        on_delete=models.PROTECT,
        related_name='orders'
    )

    accepted_quote = models.OneToOneField(
        'quotes.Quote', # Use string reference
        on_delete=models.PROTECT,
        related_name='order_created_from'
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='placed_orders',
        limit_choices_to={'role': UserRole.CUSTOMER}
    )

    manufacturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_orders',
        limit_choices_to={'role': UserRole.MANUFACTURER}
    )

    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT # Align with payment view expectation
    )

    order_total_price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery_date = models.DateField(blank=True, null=True)
    actual_ship_date = models.DateField(blank=True, null=True) # New field
    shipping_address = models.JSONField(blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipping_carrier = models.CharField(max_length=100, blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True) # New field

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Accessing related fields might cause N+1 if not pre-fetched.
        # For __str__, usually okay, but be mindful in serializers/views.
        try:
            design_name = self.design.design_name
        except models.ObjectDoesNotExist: # Or designs.models.Design.DoesNotExist if imported directly
            design_name = "N/A"

        return f"Order {self.id} for Design '{design_name}'"

    def calculate_and_set_estimated_delivery(self, quote_lead_time_days=None):
        """
        Calculates and sets the estimated delivery date based on the quote's lead time.
        Can be called during order creation.
        """
        if quote_lead_time_days is None and self.accepted_quote_id:
            # This will fetch the quote again if not already loaded.
            # It's better if lead_time is passed or quote instance is available.
            try:
                quote_lead_time_days = self.accepted_quote.estimated_lead_time_days
            except models.ObjectDoesNotExist: # Or quotes.models.Quote.DoesNotExist
                 pass # Cannot calculate if quote is gone or not linked

        if quote_lead_time_days is not None:
            # Use created_at if available (for existing orders), else timezone.now() (for new orders pre-save)
            base_date = self.created_at.date() if self.created_at else timezone.now().date()
            self.estimated_delivery_date = base_date + timedelta(days=quote_lead_time_days)
        else:
            # Fallback or leave null if no lead time available
            self.estimated_delivery_date = None


    class Meta:
        db_table = 'Orders' # As per (future) spec, assuming 'Orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['status']),
        ]
