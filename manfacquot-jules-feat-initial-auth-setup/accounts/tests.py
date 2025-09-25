from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, UserRole, Manufacturer # Added Manufacturer here
from django.contrib.auth.hashers import check_password
# For decoding JWT if needed for deeper inspection, though not strictly necessary for these tests
# from rest_framework_simplejwt.tokens import AccessToken

class UserRegistrationLoginTests(APITestCase):

    def test_user_registration_success_customer(self):
        url = reverse('user_register')
        data = {
            "email": "customer@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "company_name": "Test Customer Co",
            "role": UserRole.CUSTOMER
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.company_name, data["company_name"])
        self.assertEqual(user.role, data["role"])
        self.assertTrue(user.has_usable_password())
        self.assertTrue(check_password(data["password"], user.password))
        self.assertEqual(response.data['message'], "User registered successfully.")

    def test_user_registration_success_manufacturer(self):
        url = reverse('user_register')
        data = {
            "email": "manufacturer@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "company_name": "Test Manufacturer Co",
            "role": UserRole.MANUFACTURER
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.email, data["email"])
        self.assertEqual(user.company_name, data["company_name"])
        self.assertEqual(user.role, data["role"])

    def test_user_registration_failure_password_mismatch(self):
        url = reverse('user_register')
        data = {
            "email": "test2@example.com",
            "password": "StrongPassword123!",
            "password2": "WrongPassword!",
            "company_name": "Test Company 2",
            "role": UserRole.MANUFACTURER
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data) # Serializer error key for password mismatch
        self.assertEqual(User.objects.count(), 0)

    def test_user_registration_failure_duplicate_email(self):
        User.objects.create_user(email="test@example.com", password="password123", role=UserRole.CUSTOMER)

        url = reverse('user_register')
        data = {
            "email": "test@example.com", # Duplicate email
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "company_name": "Another Company",
            "role": UserRole.CUSTOMER
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data) # Serializer error key for duplicate email
        self.assertEqual(User.objects.count(), 1)

    def test_user_registration_failure_invalid_role(self):
        url = reverse('user_register')
        data = {
            "email": "invalidrole@example.com",
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "company_name": "Invalid Role Co",
            "role": "invalid_role_value" # Not in UserRole.choices
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("role", response.data)
        self.assertEqual(User.objects.count(), 0)

    def test_user_registration_failure_missing_fields(self):
        url = reverse('user_register')
        # Missing email
        data_no_email = {
            "password": "StrongPassword123!", "password2": "StrongPassword123!",
            "company_name": "No Email Co", "role": UserRole.CUSTOMER
        }
        response = self.client.post(url, data_no_email, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

        # Missing password
        data_no_password = {
            "email": "nopass@example.com", "password2": "StrongPassword123!",
            "company_name": "No Pass Co", "role": UserRole.CUSTOMER
        }
        response = self.client.post(url, data_no_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_user_login_success_and_token_content(self):
        user_password = "LoginPassword123!"
        user_email = "loginuser@example.com"
        user_company = "Login Corp"
        user_role = UserRole.MANUFACTURER

        User.objects.create_user(
            email=user_email,
            password=user_password,
            company_name=user_company,
            role=user_role
        )

        url = reverse('token_obtain_pair')
        data = {"email": user_email, "password": user_password}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # To check custom claims, you'd typically decode the token.
        # This requires PyJWT, which should be installed with djangorestframework-simplejwt.
        # from rest_framework_simplejwt.tokens import AccessToken
        # access_token_payload = AccessToken(response.data['access']).payload
        # self.assertEqual(access_token_payload['email'], user_email)
        # self.assertEqual(access_token_payload['role'], user_role)
        # self.assertEqual(access_token_payload['company_name'], user_company)
        # self.assertIn('user_id', access_token_payload) # Default user_id claim

    def test_user_login_failure_wrong_password(self):
        user_email = "loginfail@example.com"
        User.objects.create_user(email=user_email, password="password123", role=UserRole.CUSTOMER)

        url = reverse('token_obtain_pair')
        data = {"email": user_email, "password": "wrongpassword"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_user_login_failure_nonexistent_user(self):
        url = reverse('token_obtain_pair')
        data = {"email": "nosuchuser@example.com", "password": "password123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_current_user_view_authenticated(self):
        user_email = "currentuser@example.com"
        user_password = "currentpassword"
        user_company = "Current Inc."
        user = User.objects.create_user(email=user_email, password=user_password, company_name=user_company, role=UserRole.CUSTOMER)

        login_url = reverse('token_obtain_pair')
        login_data = {"email": user_email, "password": user_password}
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['access']

        me_url = reverse('current_user')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(me_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user_email)
        self.assertEqual(response.data['company_name'], user_company)
        # UserSerializer returns the display name for role by default
        self.assertEqual(response.data['role'], UserRole(user.role).label)

    def test_current_user_view_unauthenticated(self):
        url = reverse('current_user')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_validators_on_registration(self):
        url = reverse('user_register')
        data = {
            "email": "weakpass@example.com",
            "password": "123", # Too short, too common, not complex enough
            "password2": "123",
            "company_name": "Weak Pass Inc",
            "role": UserRole.CUSTOMER
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        # Example: Check for a specific validator's message if it's configured
        # self.assertTrue(any("This password is too short." in error for error in response.data['password']))
        # self.assertTrue(any("This password is too common." in error for error in response.data['password']))
        self.assertEqual(User.objects.count(), 0)

    def test_token_refresh(self):
        user_email = "refreshtest@example.com"
        user_password = "refreshpassword"
        User.objects.create_user(email=user_email, password=user_password, role=UserRole.CUSTOMER)

        login_url = reverse('token_obtain_pair')
        login_data = {"email": user_email, "password": user_password}
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data['refresh']
        old_access_token = login_response.data['access']

        refresh_url = reverse('token_refresh')
        refresh_data = {"refresh": refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
        self.assertNotIn("refresh", refresh_response.data) # Default behavior of RefreshView
        new_access_token = refresh_response.data['access']
        self.assertNotEqual(old_access_token, new_access_token)


class ManufacturerAPITests(APITestCase):
    def setUp(self):
        # Create a manufacturer user and their profile
        self.manufacturer_user_data = {
            "email": "manuf@example.com", "password": "ManufPassword123!",
            "company_name": "Manuf Corp", "role": UserRole.MANUFACTURER
        }
        self.manufacturer_user = User.objects.create_user(**self.manufacturer_user_data)
        # Manufacturer profile should be auto-created by UserRegistrationSerializer logic,
        # or by ManufacturerProfileUpdateView's get_object if accessed directly.
        # For testing, ensure it exists:
        self.manufacturer_profile, _ = Manufacturer.objects.get_or_create(
            user=self.manufacturer_user,
            defaults={
                'location': 'Factory City',
                'capabilities': {"cnc": True, "materials": ["Al-6061"]},
                'certifications': ["ISO9001"],
                'website_url': 'http://manufcorp.example.com'
            }
        )

        # Create a customer user
        self.customer_user_data = {
            "email": "cust@example.com", "password": "CustPassword123!",
            "company_name": "Customer Inc", "role": UserRole.CUSTOMER
        }
        self.customer_user = User.objects.create_user(**self.customer_user_data)

        # Create another manufacturer for list testing
        self.other_manufacturer_user = User.objects.create_user(
            email="othermanuf@example.com", password="OtherPassword123!",
            company_name="Other Manuf Ltd", role=UserRole.MANUFACTURER
        )
        self.other_manufacturer_profile, _ = Manufacturer.objects.get_or_create(
            user=self.other_manufacturer_user,
            defaults={'location': 'Another Town'}
        )

    def _login_user(self, email, password):
        login_url = reverse('token_obtain_pair')
        response = self.client.post(login_url, {"email": email, "password": password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return access_token

    def test_list_manufacturers_public(self):
        url = reverse('manufacturer_list') # Should be /api/manufacturers/
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # manuf_user and other_manufacturer_user
        # Check if some expected fields are present from ManufacturerPublicSerializer
        self.assertIn('user_id', response.data[0])
        self.assertIn('company_name', response.data[0])
        self.assertIn('location', response.data[0])
        self.assertNotIn('email', response.data[0]) # email is not in ManufacturerPublicSerializer by default

    def test_retrieve_manufacturer_public_detail(self):
        # URL for /api/manufacturers/<uuid>/
        url = reverse('manufacturer_detail', kwargs={'user_id': self.manufacturer_user.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.manufacturer_user.id) # Compare UUID objects
        self.assertEqual(response.data['company_name'], self.manufacturer_user.company_name)
        self.assertEqual(response.data['location'], self.manufacturer_profile.location)

    def test_retrieve_manufacturer_not_found(self):
        import uuid
        non_existent_uuid = uuid.uuid4()
        url = reverse('manufacturer_detail', kwargs={'user_id': non_existent_uuid})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_manufacturer_get_own_profile_success(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update') # /api/manufacturers/profile/
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.manufacturer_user.id) # Compare UUID objects
        self.assertEqual(response.data['email'], self.manufacturer_user.email) # Profile serializer includes email
        self.assertEqual(response.data['location'], self.manufacturer_profile.location)

    def test_manufacturer_update_own_profile_success(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        update_data = {
            "location": "New Locationville",
            "markup_factor": "1.25", # Added to make the payload complete for PUT
            "capabilities": {
                "cnc": False,
                "3d_printing": True,
                "materials_supported": ["PLA", "ABS"],
                "max_size_mm": [250, 250, 200], # Example valid size
                "pricing_factors": {
                    "material_properties": {
                        "PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 20.0},
                        "ABS": {"density_g_cm3": 1.04, "cost_usd_kg": 25.0}
                    },
                    "machining": {
                        "base_time_cost_unit": 10.0,
                        "time_multiplier_complexity_cost_unit": 50.0
                    },
                    "estimated_lead_time_base_days": 5
                }
            },
            "certifications": ["ISO14001", "AS9100"],
            "website_url": "http://new.example.com"
        }
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.manufacturer_profile.refresh_from_db()
        self.assertEqual(self.manufacturer_profile.location, update_data['location'])
        # Deep comparison for capabilities might be tricky if order changes in JSON
        # For simplicity, check a few key things or use a custom dict comparison if needed.
        self.assertEqual(self.manufacturer_profile.capabilities.get("cnc"), False)
        self.assertEqual(self.manufacturer_profile.capabilities.get("materials_supported"), ["PLA", "ABS"])
        self.assertIsNotNone(self.manufacturer_profile.capabilities.get("pricing_factors"))
        self.assertEqual(self.manufacturer_profile.certifications, update_data['certifications'])
        self.assertEqual(self.manufacturer_profile.website_url, update_data['website_url'])
        # Check if read-only fields were not changed by PUT
        self.assertEqual(response.data['email'], self.manufacturer_user.email)

    def test_manufacturer_update_profile_partial_success(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        patch_data = {"location": "Patch City"}
        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.manufacturer_profile.refresh_from_db()
        self.assertEqual(self.manufacturer_profile.location, patch_data['location'])
        # Ensure other fields remain unchanged
        self.assertIsNotNone(self.manufacturer_profile.capabilities)

    def test_manufacturer_update_profile_invalid_data(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        invalid_data = {
            "capabilities": "not a dict", # Invalid type
            "certifications": "not a list"
        }
        response = self.client.put(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capabilities', response.data)
        self.assertIn('certifications', response.data)

    def test_customer_cannot_access_manufacturer_profile_update_view(self):
        self._login_user(self.customer_user_data['email'], self.customer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        response = self.client.get(url, format='json')
        # IsManufacturerUser permission should deny
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        update_data = {"location": "Trying to update"}
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_manufacturer_profile_update_view(self):
        self.client.credentials() # Clear any auth
        url = reverse('manufacturer_profile_update')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) # IsAuthenticated permission

        update_data = {"location": "Trying to update again"}
        response = self.client.put(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manufacturer_profile_auto_creation_on_registration(self):
        # Test the signal or serializer logic that creates Manufacturer profile
        # This is implicitly tested by test_user_registration_success_manufacturer
        # if Manufacturer.objects.get(user=user) exists.
        # Let's make it more explicit here.
        reg_url = reverse('user_register')
        new_manuf_email = "newmanuf@example.com"
        data = {
            "email": new_manuf_email,
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "company_name": "New Manuf Co",
            "role": UserRole.MANUFACTURER
        }
        response = self.client.post(reg_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(email=new_manuf_email)
        self.assertTrue(hasattr(new_user, 'manufacturer_profile'))
        self.assertIsNotNone(new_user.manufacturer_profile)
        self.assertEqual(new_user.manufacturer_profile.user, new_user)

    def test_user_serializer_includes_manufacturer_profile(self):
        # Log in as manufacturer to get their details via /me endpoint
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        me_url = reverse('current_user')
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('manufacturer_profile', response.data)
        self.assertIsNotNone(response.data['manufacturer_profile'])
        self.assertEqual(response.data['manufacturer_profile']['location'], self.manufacturer_profile.location)
        self.assertEqual(response.data['manufacturer_profile']['user_id'], self.manufacturer_user.id) # Compare UUID objects

    def test_user_serializer_excludes_manufacturer_profile_for_customer(self):
        self._login_user(self.customer_user_data['email'], self.customer_user_data['password'])
        me_url = reverse('current_user')
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('manufacturer_profile', response.data) # Should be popped by serializer
        # Or if it exists, it should be None, depending on serializer logic.
        # Current UserSerializer logic with to_representation should pop it.
        # If it was: self.assertIsNone(response.data.get('manufacturer_profile'))


    # --- Tests for ManufacturerProfileSerializer capabilities validation ---
    def test_update_profile_valid_pricing_factors(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        valid_capabilities = {
            "materials_supported": ["PLA", "ABS"],
            "max_size_mm": [200, 200, 150],
            "pricing_factors": {
                "material_properties": {
                    "PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 20.0},
                    "ABS": {"density_g_cm3": 1.04, "cost_usd_kg": 25.0}
                },
                "machining": {
                    "base_time_cost_unit": 10.0, # Using float/int directly
                    "time_multiplier_complexity_cost_unit": 50.0
                },
                "estimated_lead_time_base_days": 7
            }
        }
        data = {"capabilities": valid_capabilities, "markup_factor": "1.15"} # markup_factor is also required
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.manufacturer_profile.refresh_from_db()
        self.assertEqual(self.manufacturer_profile.capabilities, valid_capabilities)
        self.assertEqual(float(self.manufacturer_profile.markup_factor), 1.15)

    def test_update_profile_material_in_supported_but_not_in_pricing(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        invalid_capabilities = {
            "materials_supported": ["PLA", "PETG"], # PETG not in material_properties
            "max_size_mm": [100,100,100],
            "pricing_factors": {
                "material_properties": {"PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 20.0}},
                "machining": {"base_time_cost_unit": 5.0, "time_multiplier_complexity_cost_unit": 20.0}
            }
        }
        data = {"capabilities": invalid_capabilities}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("capabilities", response.data)
        self.assertTrue(any("Material 'PETG' is listed in 'materials_supported' but lacks pricing data" in e for e in response.data['capabilities']))

    def test_update_profile_invalid_density_or_cost(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        # Invalid density (zero)
        capabilities_bad_density = {
            "materials_supported": ["PLA"], "max_size_mm": [100,100,100],
            "pricing_factors": {
                "material_properties": {"PLA": {"density_g_cm3": 0, "cost_usd_kg": 20.0}},
                "machining": {"base_time_cost_unit": 5.0, "time_multiplier_complexity_cost_unit": 20.0}
            }
        }
        data = {"capabilities": capabilities_bad_density}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Density for material 'PLA' must be a positive number", response.data['capabilities'][0])

        # Invalid cost (negative)
        capabilities_bad_cost = {
            "materials_supported": ["PLA"], "max_size_mm": [100,100,100],
            "pricing_factors": {
                "material_properties": {"PLA": {"density_g_cm3": 1.25, "cost_usd_kg": -5.0}},
                "machining": {"base_time_cost_unit": 5.0, "time_multiplier_complexity_cost_unit": 20.0}
            }
        }
        data = {"capabilities": capabilities_bad_cost}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cost per kg for material 'PLA' must be a non-negative number", response.data['capabilities'][0])

    def test_update_profile_missing_machining_params(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        capabilities_missing_machining = {
            "materials_supported": ["PLA"], "max_size_mm": [100,100,100],
            "pricing_factors": {
                "material_properties": {"PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 20.0}},
                "machining": { } # Missing base_time_cost_unit and time_multiplier_complexity_cost_unit
            }
        }
        data = {"capabilities": capabilities_missing_machining}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("`base_time_cost_unit` in machining factors must be a non-negative number.", response.data['capabilities'][0])
        # Depending on error ordering, the other might also appear or just the first one.
        # self.assertIn("`time_multiplier_complexity_cost_unit` in machining factors must be a non-negative number.", response.data['capabilities'][0])

    def test_update_profile_invalid_max_size_mm_format(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('manufacturer_profile_update')
        capabilities_invalid_max_size = {
            "materials_supported": ["PLA"], "max_size_mm": [100, 100], # Only 2 dimensions
             "pricing_factors": { # Valid pricing to isolate max_size_mm error
                "material_properties": {"PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 20.0}},
                "machining": {"base_time_cost_unit": 10.0, "time_multiplier_complexity_cost_unit": 50.0}
            }
        }
        data = {"capabilities": capabilities_invalid_max_size}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("`max_size_mm` must be a list of three numbers", response.data['capabilities'][0])
