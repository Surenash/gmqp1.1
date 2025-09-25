import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserRole(models.TextChoices):
    CUSTOMER = 'customer', 'Customer'
    MANUFACTURER = 'manufacturer', 'Manufacturer'

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role=UserRole.CUSTOMER, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password) # Hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Role for superuser can be customer or a specific admin role if you add one.
        # For GMQP, a superuser might not directly fit 'customer' or 'manufacturer' roles
        # in terms of business logic, but a role is needed.
        # Defaulting to customer here, but this could be an 'admin' role if added to UserRole.
        extra_fields.setdefault('role', UserRole.CUSTOMER)


        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # We don't pass role directly to create_user if it's already in extra_fields
        role_to_pass = extra_fields.pop('role')
        return self.create_user(email, password, role=role_to_pass, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    # password_hash is handled by AbstractBaseUser's password field
    company_name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        # Default role should be set based on your registration flow.
        # If registration allows choosing, this default might be less critical.
        # Defaulting to CUSTOMER as per spec's UserRole enum.
        default=UserRole.CUSTOMER,
    )
    is_active = models.BooleanField(default=True) # User is active by default
    is_staff = models.BooleanField(default=False) # For Django admin access

    # Renaming created_at from spec to align with Django conventions (auto_now_add)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # For PermissionsMixin, Django expects these related_names if you don't explicitly set them.
    # If you get clashes, you'll need to add related_name arguments.
    # groups = models.ManyToManyField('auth.Group', related_name='custom_user_groups', blank=True)
    # user_permissions = models.ManyToManyField('auth.Permission', related_name='custom_user_permissions', blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email' # Use email as the unique identifier
    REQUIRED_FIELDS = ['company_name'] # e.g., company_name required for createsuperuser, adjust as needed

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'Users' # To match the spec's table name
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class Manufacturer(models.Model):
    # user_id UUID PRIMARY KEY REFERENCES Users(id)
    # Using OneToOneField to User, which implies a unique link and can act as PK.
    # The User's id (UUID) will effectively be the Manufacturer's id.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='manufacturer_profile' # Allows access via user.manufacturer_profile
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    # capabilities JSONB, -- e.g., {"cnc": true, "materials": ["Al-6061", "ABS"], "max_size_mm": [500, 300, 200]}
    capabilities = models.JSONField(blank=True, null=True)
    # certifications TEXT[],
    # Using Django's ArrayField requires PostgreSQL.
    # For simplicity with SQLite in dev, this could be a JSONField or CommaSeparatedIntegerField.
    # However, spec says PostgreSQL, so ArrayField is appropriate.
    # For now, I'll use JSONField to store a list of strings to maintain compatibility
    # if the underlying DB isn't PostgreSQL during early dev, and it can be migrated later.
    # If direct PostgreSQL ArrayField is desired from the start, and environment supports it:
    # from django.contrib.postgres.fields import ArrayField
    # certifications = ArrayField(models.TextField(), blank=True, null=True)
    certifications = models.JSONField(blank=True, null=True, default=list) # Stores a list of strings

    # average_rating NUMERIC(2, 1) DEFAULT 0.0
    average_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)
    website_url = models.URLField(max_length=255, blank=True, null=True)

    # Pricing specific fields
    # manufacturer_markup_factor (e.g., 1.2 for 20% markup)
    markup_factor = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        help_text="General markup factor applied to total cost (e.g., 1.2 for 20% markup)."
    )
    # Other pricing parameters like material costs, densities, base_time, time_multiplier
    # will be stored in the 'capabilities' JSONField under a 'pricing_factors' key.
    # Example: capabilities = { "pricing_factors": { "material_properties": {...}, "machining": {...} } }


    # Timestamps (optional, but good practice)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.company_name or self.user.email}'s Manufacturer Profile"

    class Meta:
        db_table = 'Manufacturers' # To match the spec's table name
        verbose_name = 'Manufacturer'
        verbose_name_plural = 'Manufacturers'
