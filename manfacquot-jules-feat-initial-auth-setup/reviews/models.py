import uuid
from django.db import models
from django.conf import settings # For AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import UserRole # Assuming this is the correct path

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews',
        limit_choices_to={'role': UserRole.CUSTOMER}
    )

    manufacturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reviews',
        limit_choices_to={'role': UserRole.MANUFACTURER}
    )

    # order_id is optional. If it becomes a ForeignKey to an 'Orders' table later,
    # ensure on_delete behavior is defined (e.g., models.SET_NULL if review should persist).
    order_id = models.UUIDField(blank=True, null=True)

    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message=_("Rating must be at least 1.")),
            MaxValueValidator(5, message=_("Rating must be at most 5."))
        ]
    )

    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        customer_display = getattr(self.customer, 'company_name', None) or self.customer.email
        manufacturer_display = getattr(self.manufacturer, 'company_name', None) or self.manufacturer.email
        return f"Review by {customer_display} for {manufacturer_display} ({self.rating}/5)"

    class Meta:
        db_table = 'Reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        # Consider unique constraints based on business rules, e.g.,
        # unique_together = [['customer', 'manufacturer', 'order_id']]
        # This would require order_id to be non-null for the constraint to be most effective,
        # or handle nulls specifically if your DB supports it (e.g. PostgreSQL's unique nulls).
        # For now, allowing multiple reviews from same customer to same manufacturer if order_id differs or is null.
        # If order_id is always null initially, a customer could review a manufacturer multiple times.
        # This might be desired or not. If not, unique_together = [['customer', 'manufacturer']]
        # could be used if reviews are not tied to orders.
        # For now, no unique_together constraint is set, allowing flexibility.
        # Business logic for preventing duplicate reviews can be handled in serializers/views if needed.
        pass
