from rest_framework import serializers
from .models import Quote, QuoteStatus
from designs.models import Design
from accounts.models import User, UserRole # For validation and representation

class QuoteSerializer(serializers.ModelSerializer):
    # Display related object details rather than just PKs
    design_name = serializers.CharField(source='design.design_name', read_only=True)
    # manufacturer_company_name = serializers.CharField(source='manufacturer.company_name', read_only=True)
    # To handle potential blank company_name for manufacturer:
    manufacturer_display_name = serializers.SerializerMethodField(read_only=True)

    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Allow design and manufacturer to be set by ID on create/update
    # design = serializers.PrimaryKeyRelatedField(queryset=Design.objects.all()) # Simpler alternative
    # manufacturer = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=UserRole.MANUFACTURER))

    class Meta:
        model = Quote
        fields = [
            'id',
            'design', # Use PrimaryKeyRelatedField or SlugRelatedField if writing by ID
            'design_name',
            'manufacturer', # Similar for manufacturer
            'manufacturer_display_name',
            'price_usd',
            'estimated_lead_time_days',
            'status',
            'status_display',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'design_name', 'manufacturer_display_name',
            'status_display', 'created_at', 'updated_at',
            'design', 'manufacturer' # Make these read-only as they are set by the view context
        ]
        # `status` can be updated, e.g., by customer accepting/rejecting or manufacturer.

    def get_manufacturer_display_name(self, obj):
        # Safely get company_name or fall back to email
        return obj.manufacturer.company_name or obj.manufacturer.email

    def validate_manufacturer(self, value):
        """Ensure the manufacturer user has the 'manufacturer' role."""
        if value.role != UserRole.MANUFACTURER:
            raise serializers.ValidationError("Quotes can only be associated with Manufacturer users.")
        return value

    def validate_design(self, value):
        """
        Optional: Add validation for the design, e.g., ensure it's in a state ready for quotes.
        For example, design status should ideally be 'ANALYSIS_COMPLETE'.
        """
        # from designs.models import DesignStatus # Local import
        # if value.status != DesignStatus.ANALYSIS_COMPLETE:
        #     raise serializers.ValidationError(
        #         f"Design must be in '{DesignStatus.ANALYSIS_COMPLETE.label}' status to receive quotes. Current status: {value.get_status_display()}"
        #     )
        return value

    def validate(self, data):
        """
        Object-level validation.
        Example: Ensure the manufacturer creating the quote is not the customer who owns the design.
        """
        request = self.context.get('request')
        design = data.get('design') or (self.instance.design if self.instance else None)
        manufacturer_user = data.get('manufacturer') or (self.instance.manufacturer if self.instance else None)

        if design and manufacturer_user:
            if design.customer == manufacturer_user:
                raise serializers.ValidationError("A manufacturer cannot create a quote for their own design.")

        # If creating (no instance), the view's perform_create will set the manufacturer.
        # The CanCreateQuoteForDesign permission already ensures request.user is a manufacturer.
        # This specific check for request.user == manufacturer_user might be problematic if manufacturer
        # is not expected in `data` due to being read_only and set by view.
        # Consider if this validation is still needed here or if view/permission handles it.
        # If manufacturer_user is None (because it's read_only and not in data), this would fail.
        # For now, let's assume the view correctly sets the manufacturer.
        # If 'manufacturer' was part of 'data', then this check would be:
        # if not self.instance and request and request.user and manufacturer_user:
        #     if request.user != manufacturer_user:
        #          raise serializers.ValidationError("The logged-in user must match the manufacturer specified in the quote.")
        #     if request.user.role != UserRole.MANUFACTURER: # Redundant if CanCreateQuoteForDesign is used
        #         raise serializers.ValidationError("Only manufacturers can create quotes.")

        # If updating status
        if self.instance and 'status' in data:
            current_status = self.instance.status
            new_status = data['status']
            # Add logic for allowed status transitions based on user role (customer vs manufacturer)
            # Example: Customer can change PENDING -> ACCEPTED/REJECTED
            # Manufacturer might change PENDING -> EXPIRED (if system doesn't do it automatically)
            if request and request.user:
                if request.user == design.customer: # Customer is acting
                    if current_status == QuoteStatus.PENDING and new_status not in [QuoteStatus.ACCEPTED, QuoteStatus.REJECTED]:
                        raise serializers.ValidationError(f"Customer can only change status to Accepted or Rejected from Pending. Invalid transition to {new_status}.")
                elif request.user == manufacturer_user: # Manufacturer is acting
                    # Manufacturers typically don't change status after creation, except maybe to withdraw/expire manually
                    if new_status != current_status and new_status != QuoteStatus.EXPIRED : # Example
                         raise serializers.ValidationError(f"Manufacturer cannot change status to {new_status} this way.")
                else: # Some other user
                    raise serializers.ValidationError("You do not have permission to change the status of this quote.")

        return data
