from rest_framework import serializers
from .models import Review
from accounts.models import User, UserRole # For validation and representation

class ReviewSerializer(serializers.ModelSerializer):
    customer_display_name = serializers.SerializerMethodField(read_only=True)
    # manufacturer_company_name = serializers.CharField(source='manufacturer.company_name', read_only=True)
    # To handle potential blank company_name for manufacturer:
    manufacturer_display_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'customer', # FK, writeable for association, but usually set from request.user
            'customer_display_name',
            'manufacturer', # FK, writeable by ID
            'manufacturer_display_name',
            'order_id', # Optional UUID
            'rating',
            'comment',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'customer_display_name', 'manufacturer_display_name', 'created_at', 'updated_at']
        # 'customer' is often set implicitly from request.user.
        # 'manufacturer' is typically part of the URL or payload for creation.

    def get_customer_display_name(self, obj):
        return obj.customer.company_name or obj.customer.email

    def get_manufacturer_display_name(self, obj):
        return obj.manufacturer.company_name or obj.manufacturer.email

    def validate_customer(self, value):
        """Ensure the customer user has the 'customer' role."""
        if value.role != UserRole.CUSTOMER:
            raise serializers.ValidationError("Reviews can only be submitted by Customer users.")
        return value

    def validate_manufacturer(self, value):
        """Ensure the manufacturer user has the 'manufacturer' role."""
        if value.role != UserRole.MANUFACTURER:
            raise serializers.ValidationError("Reviews can only be for Manufacturer users.")
        return value

    def validate_rating(self, value):
        """Additional check though model validator also exists."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        """
        Object-level validation.
        - Ensure the customer creating the review is the logged-in user.
        - Prevent duplicate reviews (e.g., one review per customer per manufacturer/order).
        """
        request = self.context.get('request')

        # On create, ensure the customer is the logged-in user
        if not self.instance and request and request.user:
            # If 'customer' is part of the payload, ensure it matches request.user
            if 'customer' in data and data['customer'] != request.user:
                raise serializers.ValidationError({"customer": "You can only submit reviews as yourself."})
            # If 'customer' is not in payload, it will be set from request.user in view/serializer.create
            if request.user.role != UserRole.CUSTOMER:
                 raise serializers.ValidationError("Only customers can submit reviews.")

        # Prevent duplicate reviews (example: one review per customer per manufacturer)
        # This logic might be more complex depending on whether order_id is considered.
        # If order_id is null, this means one review per customer per manufacturer.
        # If order_id is present, one review per customer per manufacturer per order.
        # The current model allows multiple reviews if this isn't checked.

        # For simplicity, let's check for one review per customer per manufacturer if no order_id.
        # More complex logic might be needed if order_id is sometimes present.
        # This check is primarily for creation (not self.instance).
        if not self.instance:
            customer = request.user if request else data.get('customer')
            manufacturer = data.get('manufacturer')
            order_id = data.get('order_id')

            query = Review.objects.filter(customer=customer, manufacturer=manufacturer)
            if order_id:
                query = query.filter(order_id=order_id)
            else:
                # If creating a review without an order_id, check if a non-order-specific review already exists
                query = query.filter(order_id__isnull=True)

            if query.exists():
                if order_id:
                    raise serializers.ValidationError(
                        "A review for this manufacturer and order already exists."
                    )
                else:
                    raise serializers.ValidationError(
                        "You have already submitted a review for this manufacturer (without a specific order reference)."
                    )
        return data

    def create(self, validated_data):
        """
        Set customer from the request context if not already set by validation.
        """
        if 'request' in self.context and not validated_data.get('customer'):
            validated_data['customer'] = self.context['request'].user

        # Ensure the user being associated is indeed a customer
        user = validated_data.get('customer')
        if user and user.role != UserRole.CUSTOMER:
             raise serializers.ValidationError({
                 "customer": "Reviews can only be submitted by Customer users."
             })
        return super().create(validated_data)
