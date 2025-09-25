import uuid
from django.db import models
from django.conf import settings # To reference AUTH_USER_MODEL
from django.utils.translation import gettext_lazy as _

# From spec: CREATE TYPE design_status AS ENUM ('pending_analysis', 'analysis_complete', 'quoted', 'ordered');
class DesignStatus(models.TextChoices):
    PENDING_ANALYSIS = 'pending_analysis', _('Pending Analysis')
    ANALYSIS_COMPLETE = 'analysis_complete', _('Analysis Complete')
    ANALYSIS_FAILED = 'analysis_failed', _('Analysis Failed') # New status
    QUOTED = 'quoted', _('Quoted')
    ORDERED = 'ordered', _('Ordered')

class Design(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # customer_id UUID NOT NULL REFERENCES Users(id),
    # The ForeignKey will create a 'customer_id' column.
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='designs'
        # If we need to ensure only 'customer' role users:
        # limit_choices_to={'role': 'customer'}
        # This is a DB constraint. Validation should also be in serializer/view.
    )
    design_name = models.CharField(max_length=255)
    s3_file_key = models.CharField(max_length=1024)
    material = models.CharField(max_length=100)
    quantity = models.IntegerField()

    status = models.CharField(
        max_length=20, # Max length of enum values
        choices=DesignStatus.choices,
        default=DesignStatus.PENDING_ANALYSIS,
    )
    geometric_data = models.JSONField(blank=True, null=True) # To store analysis results
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Good practice, though not in spec explicitly for this table

    def __str__(self):
        return f"{self.design_name} (Customer: {self.customer.get_username()})" # Using get_username() for flexibility

    class Meta:
        db_table = 'Designs' # To match spec table name
        verbose_name = 'Design'
        verbose_name_plural = 'Designs'
        ordering = ['-created_at']
        # Django automatically creates an index on ForeignKey fields (like customer_id),
        # so CREATE INDEX idx_designs_customer_id ON Designs(customer_id); is covered.
