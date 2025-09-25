from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserSerializer
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny] # Anyone can register

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # According to spec, just a success message or tokens.
            # Returning a simple success message.
            return Response({
                "message": "User registered successfully.",
                # "user_id": user.id, # Optionally return user id or other details
                # "email": user.email,
                # "role": user.role
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the token as per spec or future needs
        token['email'] = user.email
        token['role'] = user.role
        if user.company_name:
            token['company_name'] = user.company_name
        return token

    # If you need to customize the response structure of the token endpoint itself
    # (not just the token payload), you can do it here.
    # def validate(self, attrs):
    #     data = super().validate(attrs)
    #     # Example: adding user details alongside tokens in the response
    #     # data['user'] = {
    #     #     'id': self.user.id,
    #     #     'email': self.user.email,
    #     #     'role': self.user.role,
    #     #     'company_name': self.user.company_name
    #     # }
    #     return data

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    Corresponds to POST /api/auth/token
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny] # Default for TokenObtainPairView


# Example of a protected view to get current user details
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Ensures only authenticated users can access

    def get_object(self):
        # Returns the current authenticated user
        return self.request.user


# --- Manufacturer Views ---
from .models import Manufacturer, UserRole
from .serializers import ManufacturerProfileSerializer, ManufacturerPublicSerializer
from rest_framework.permissions import BasePermission

class IsManufacturerUser(BasePermission):
    """
    Allows access only to users with the 'manufacturer' role.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.MANUFACTURER)

class ManufacturerListView(generics.ListAPIView):
    """
    GET /api/manufacturers
    Lists all manufacturers (publicly accessible details).
    Supports filtering by capability and material (to be implemented).
    """
    queryset = Manufacturer.objects.select_related('user').all() # Optimize by fetching user details
    serializer_class = ManufacturerPublicSerializer
    permission_classes = [AllowAny] # As per spec, "Get a list of all vetted manufacturers"

    # TODO: Implement filtering based on query parameters like ?capability=cnc&material=Al-6061
    # This can be done by overriding get_queryset method or using django-filter library.
    # For now, it returns all manufacturers.

class ManufacturerDetailView(generics.RetrieveAPIView):
    """
    GET /api/manufacturers/{id} (where id is User UUID)
    Gets the detailed public profile for a specific manufacturer.
    """
    queryset = Manufacturer.objects.select_related('user').all()
    serializer_class = ManufacturerPublicSerializer
    permission_classes = [AllowAny] # Publicly accessible
    lookup_field = 'user_id' # The Manufacturer PK is user_id

class ManufacturerProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET, PUT, PATCH /api/manufacturers/profile
    Allows a manufacturer to view and update their own profile.
    """
    serializer_class = ManufacturerProfileSerializer
    permission_classes = [IsAuthenticated, IsManufacturerUser]

    def get_object(self):
        # Ensure the manufacturer profile exists, or create if it doesn't (should be created on registration)
        # This also handles the case where a user might have been switched to manufacturer role later.
        manufacturer_profile, created = Manufacturer.objects.get_or_create(user=self.request.user)
        if created:
            # If created, it means it wasn't made during registration for some reason.
            # Log this or handle as an edge case. For now, just return it.
            pass
        return manufacturer_profile

    def get_queryset(self):
        # This method is not strictly necessary for RetrieveUpdateAPIView if get_object is overridden
        # but it's good practice to define it.
        return Manufacturer.objects.filter(user=self.request.user)
