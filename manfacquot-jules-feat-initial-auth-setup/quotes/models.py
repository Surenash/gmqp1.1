import uuid
from django.db import models
from django.conf import settings # For AUTH_USER_MODEL
from django.utils.translation import gettext_lazy as _
from designs.models import Design
# Assuming accounts.models.UserRole is the correct path for UserRole enum
from accounts.models import UserRole

# From spec: CREATE TYPE quote_status AS ENUM ('pending', 'accepted', 'rejected', 'expired');
class QuoteStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    ACCEPTED = 'accepted', _('Accepted')
    REJECTED = 'rejected', _('Rejected')
    EXPIRED = 'expired', _('Expired')

class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name='quotes'
    )

    # manufacturer links to a User with role 'manufacturer'
    manufacturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_quotes',
        # This ensures that the selected user for 'manufacturer' field must have the role 'manufacturer'.
        limit_choices_to={'role': UserRole.MANUFACTURER}
    )

    price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_lead_time_days = models.IntegerField()

    status = models.CharField(
        max_length=10, # Longest value is 'accepted' (8 chars) or 'rejected' (8 chars)
        choices=QuoteStatus.choices,
        default=QuoteStatus.PENDING,
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # manufacturer.company_name might not exist if User model doesn't guarantee it.
        # Using manufacturer.email or a method on User model that provides a display name.
        manufacturer_display_name = getattr(self.manufacturer, 'company_name', self.manufacturer.email)
        if not manufacturer_display_name: # Fallback if company_name is blank
            manufacturer_display_name = self.manufacturer.email

        return f"Quote for '{self.design.design_name}' by {manufacturer_display_name}"

    class Meta:
        db_table = 'Quotes'
        verbose_name = 'Quote'
        verbose_name_plural = 'Quotes'
        ordering = ['-created_at']
        # Django automatically creates indexes for ForeignKeys.
        # If specific compound indexes are needed beyond single FK indexes:
        # indexes = [
        #     models.Index(fields=['design', 'manufacturer']),
        # ]
        # The spec mentions idx_quotes_design_id and idx_quotes_manufacturer_id,
        # these are automatically created by Django for the ForeignKey fields.
        pass
