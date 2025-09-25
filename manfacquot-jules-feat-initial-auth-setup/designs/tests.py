import uuid
import boto3 # Import boto3
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings

# It's better to import User and UserRole from where they are defined, e.g., settings.AUTH_USER_MODEL or accounts.models
from accounts.models import User, UserRole
from .models import Design, DesignStatus
# Serializers are not strictly needed for API tests if you test request/response data,
# but can be useful for understanding expected structures or for direct serializer tests.
# from .serializers import DesignSerializer, DesignCreateSerializer # Can be useful for direct serializer tests
from accounts.models import Manufacturer # For setting up manufacturer profiles
from quotes.models import Quote # For checking if quotes are created

# Mock boto3.session.Config if it's causing issues in tests or if not easily mockable via boto3.client patch
# For example, if boto3.session.Config itself tries to load credentials.
# However, patching boto3.client should generally be sufficient for presigned URL tests.

class DesignAPITests(APITestCase):

    def setUp(self):
        # Customer User 1
        self.customer_user1_data = {
            "email": "customer1@example.com", "password": "Password123!",
            "company_name": "Customer1 Corp", "role": UserRole.CUSTOMER
        }
        self.customer_user1 = User.objects.create_user(**self.customer_user1_data)

        # Customer User 2
        self.customer_user2_data = {
            "email": "customer2@example.com", "password": "Password123!",
            "company_name": "Customer2 Ltd", "role": UserRole.CUSTOMER
        }
        self.customer_user2 = User.objects.create_user(**self.customer_user2_data)

        # Manufacturer User (should not be able to create designs)
        self.manufacturer_user_data = {
            "email": "manufacturer_designs@example.com", # Unique email
            "password": "Password123!",
            "company_name": "Manuf Designs Inc", "role": UserRole.MANUFACTURER
        }
        # Ensure this manufacturer also has a profile, as per previous module logic
        self.manufacturer_user = User.objects.create_user(**self.manufacturer_user_data)
        # Manufacturer profile would be auto-created if registration serializer was used.
        # For direct user creation, ensure profile exists if other tests depend on it.
        self.manufacturer_profile = Manufacturer.objects.create(user=self.manufacturer_user, markup_factor="1.2")


        # A design for customer1
        self.design1_c1 = Design.objects.create(
            customer=self.customer_user1,
            design_name="Test Design 1 for C1",
            s3_file_key=f"uploads/designs/{self.customer_user1.id}/test_design1.stl", # Example key
            material="ABS", # This material name should exist in manufacturer's capabilities for pricing
            quantity=10,
            status=DesignStatus.PENDING_ANALYSIS # Default, but explicit here
        )

        self.design_analyzed_c1 = Design.objects.create(
            customer=self.customer_user1,
            design_name="Analyzed Design for Quote Gen",
            s3_file_key=f"uploads/designs/{self.customer_user1.id}/analyzed_design.stl",
            material="ABS",
            quantity=20,
            status=DesignStatus.ANALYSIS_COMPLETE,
            geometric_data={
                "volume_cm3": 100.0,
                "complexity_score": 0.5,
                # Other fields like bbox, surface_area can be added if needed by tests
            }
        )


    def _login_user(self, email, password):
        login_url = reverse('token_obtain_pair')
        response = self.client.post(login_url, {"email": email, "password": password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to login user {email} for test setup.")
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        return access_token

    # --- Test S3 Pre-signed URL Generation ---
    @patch('boto3.client') # Mocks boto3.client call within the view
    def test_generate_presigned_url_success(self, mock_boto_client_constructor):
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])

        # Configure the mock S3 client that boto3.client() will return
        mock_s3_instance = MagicMock()
        mock_s3_instance.generate_presigned_url.return_value = "http://s3.mock.url/signed-upload"
        mock_boto_client_constructor.return_value = mock_s3_instance

        url = reverse('design_upload_url')
        data = {"fileName": "my_part.stl", "fileType": "model/stl"}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("uploadUrl", response.data)
        self.assertIn("s3Key", response.data)
        self.assertEqual(response.data["uploadUrl"], "http://s3.mock.url/signed-upload")

        expected_s3_key_prefix = f"{settings.AWS_S3_DESIGNS_UPLOAD_PREFIX.strip('/')}/{self.customer_user1.id}/"
        self.assertTrue(response.data["s3Key"].startswith(expected_s3_key_prefix))
        self.assertTrue(response.data["s3Key"].endswith(".stl"))

        # Check that boto3.client was called with expected AWS settings
        # Check that boto3.client was called
        self.assertEqual(mock_boto_client_constructor.call_count, 1)
        # Get the actual call arguments
        args, kwargs = mock_boto_client_constructor.call_args

        # Assert the positional argument
        self.assertEqual(args[0], 's3')

        # Assert the keyword arguments, checking config object's attribute
        self.assertEqual(kwargs['aws_access_key_id'], settings.AWS_ACCESS_KEY_ID)
        self.assertEqual(kwargs['aws_secret_access_key'], settings.AWS_SECRET_ACCESS_KEY)
        self.assertEqual(kwargs['region_name'], settings.AWS_S3_REGION_NAME)
        self.assertEqual(kwargs['endpoint_url'], settings.AWS_S3_ENDPOINT_URL)
        self.assertIsInstance(kwargs['config'], boto3.session.Config)
        self.assertEqual(kwargs['config'].signature_version, settings.AWS_S3_SIGNATURE_VERSION)

        # Check that generate_presigned_url was called on the mock_s3_instance
        mock_s3_instance.generate_presigned_url.assert_called_once_with(
            ClientMethod='put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': response.data["s3Key"], # Use the actual key generated for this check
                'ContentType': 'model/stl'
            },
            ExpiresIn=settings.AWS_S3_PRESIGNED_URL_EXPIRATION,
            HttpMethod='PUT'
        )

    def test_generate_presigned_url_unauthenticated(self):
        self.client.credentials()
        url = reverse('design_upload_url')
        data = {"fileName": "my_part.stl", "fileType": "model/stl"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_presigned_url_missing_filename(self):
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        url = reverse('design_upload_url')
        data = {"fileType": "model/stl"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "fileName is required.")

    # --- Test Design CRUD ---
    @patch('designs.tasks.analyze_cad_file.delay') # Mock the celery task's delay method
    def test_create_design_success(self, mock_analyze_task_delay):
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        url = reverse('design_list_create')
        # s3_key would be obtained from the /upload-url endpoint in a real flow
        s3_key = f"{settings.AWS_S3_DESIGNS_UPLOAD_PREFIX.strip('/')}/{self.customer_user1.id}/{uuid.uuid4()}.stl"
        data = {
            "design_name": "New Awesome Part",
            "s3_file_key": s3_key,
            "material": "PLA",
            "quantity": 50
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # setUp creates 2 designs (design1_c1, design_analyzed_c1)
        # This test creates 1 more.
        self.assertEqual(Design.objects.count(), 3)
        new_design = Design.objects.get(id=response.data['id'])
        self.assertEqual(new_design.customer, self.customer_user1)
        self.assertEqual(new_design.design_name, data['design_name'])
        self.assertEqual(new_design.s3_file_key, data['s3_file_key'])
        self.assertEqual(new_design.material, data['material'])
        self.assertEqual(new_design.quantity, data['quantity'])
        self.assertEqual(new_design.status, DesignStatus.PENDING_ANALYSIS)
        self.assertIsNone(new_design.geometric_data)
        mock_analyze_task_delay.assert_called_once_with(new_design.id)

    def test_create_design_by_manufacturer_forbidden(self):
        self._login_user(self.manufacturer_user_data['email'], self.manufacturer_user_data['password'])
        url = reverse('design_list_create')
        s3_key = f"{settings.AWS_S3_DESIGNS_UPLOAD_PREFIX.strip('/')}/{self.manufacturer_user.id}/{uuid.uuid4()}.stl"
        data = {"design_name": "Manuf Part", "s3_file_key": s3_key, "material": "Steel", "quantity": 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_own_designs(self):
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        Design.objects.create(
            customer=self.customer_user1, design_name="Design 2 C1",
            s3_file_key="key2", material="PETG", quantity=5
        )
        url = reverse('design_list_create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # customer_user1 has design1_c1 & design_analyzed_c1 from setUp, plus "Design 2 C1" created here. Total 3.
        self.assertEqual(len(response.data), 3)
        design_names_in_response = [item['design_name'] for item in response.data]
        self.assertIn("Test Design 1 for C1", design_names_in_response) # From setUp
        self.assertIn("Analyzed Design for Quote Gen", design_names_in_response) # From setUp
        self.assertIn("Design 2 C1", design_names_in_response) # Created in this test

    def test_list_designs_no_designs_for_other_customer(self): # Renamed for clarity
        self._login_user(self.customer_user2_data['email'], self.customer_user2_data['password'])
        url = reverse('design_list_create')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_retrieve_own_design_detail(self):
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        url = reverse('design_detail', kwargs={'id': self.design1_c1.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(uuid.UUID(response.data['id']), self.design1_c1.id) # Compare UUID objects
        self.assertEqual(response.data['design_name'], self.design1_c1.design_name)
        self.assertEqual(response.data['customer_email'], self.customer_user1.email)

    def test_retrieve_other_customer_design_detail_forbidden(self): # Renamed for clarity
        self._login_user(self.customer_user2_data['email'], self.customer_user2_data['password'])
        url = reverse('design_detail', kwargs={'id': self.design1_c1.id})
        response = self.client.get(url, format='json')
        # IsOwnerOrAdmin permission should result in 404 as if the object doesn't exist for this user
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_design_partial_patch(self): # Renamed for clarity
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        url = reverse('design_detail', kwargs={'id': self.design1_c1.id})
        patch_data = {
            "design_name": "Updated Design Name via PATCH",
            "quantity": 12
        }
        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.design1_c1.refresh_from_db()
        self.assertEqual(self.design1_c1.design_name, patch_data['design_name'])
        self.assertEqual(self.design1_c1.quantity, patch_data['quantity'])
        self.assertEqual(self.design1_c1.material, "ABS")

    def test_delete_own_design(self):
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        design_id_to_delete = self.design1_c1.id
        url = reverse('design_detail', kwargs={'id': design_id_to_delete})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Design.objects.filter(id=design_id_to_delete).exists())
        # design_analyzed_c1 still exists for customer_user1
        self.assertEqual(Design.objects.filter(customer=self.customer_user1).count(), 1)

    def test_delete_other_customer_design_forbidden(self):
        self._login_user(self.customer_user2_data['email'], self.customer_user2_data['password'])
        url = reverse('design_detail', kwargs={'id': self.design1_c1.id})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Design.objects.filter(id=self.design1_c1.id).exists())

    def test_create_design_missing_required_fields(self): # Renamed for clarity
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        url = reverse('design_list_create')
        # Missing s3_file_key
        data_no_s3 = { "design_name": "No Key Part", "material": "Iron", "quantity": 2 }
        response_no_s3 = self.client.post(url, data_no_s3, format='json')
        self.assertEqual(response_no_s3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('s3_file_key', response_no_s3.data)

        # Missing design_name
        s3_key = f"{settings.AWS_S3_DESIGNS_UPLOAD_PREFIX.strip('/')}/{self.customer_user1.id}/{uuid.uuid4()}.stl"
        data_no_name = { "s3_file_key": s3_key, "material": "Iron", "quantity": 2 }
        response_no_name = self.client.post(url, data_no_name, format='json')
        self.assertEqual(response_no_name.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('design_name', response_no_name.data)

    # Example of how to test s3_file_key validation if it becomes more complex
    # @patch('boto3.client')
    # def test_create_design_s3_key_prefix_mismatch(self, mock_boto_client_constructor):
    #     self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
    #     url = reverse('design_list_create')
    #     invalid_s3_key = f"wrong_prefix/{self.customer_user1.id}/{uuid.uuid4()}.stl"
    #     data = {
    #         "design_name": "Prefix Test",
    #         "s3_file_key": invalid_s3_key,
    #         "material": "TestMat", "quantity": 1
    #     }
    #     # This test requires DesignCreateSerializer to have context['request'] and validation logic for prefix
    #     # response = self.client.post(url, data, format='json')
    #     # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     # self.assertIn('s3_file_key', response.data)
    #     # self.assertIn("does not match expected user path", str(response.data['s3_file_key']))
    #     pass # Placeholder as the validation is commented out in serializer


    @patch('designs.tasks.analyze_cad_file.delay')
    def test_task_triggered_on_design_creation_api(self, mock_analyze_task_delay): # Renamed for clarity
        # This test was moved from DesignAnalysisTaskTests to DesignAPITests
        # as it tests API behavior (triggering a task).
        # It needs a logged-in user, which self.customer_user1 can serve as.
        self._login_user(self.customer_user1_data['email'], self.customer_user1_data['password'])
        url = reverse('design_list_create')
        s3_key = f"uploads/designs/{self.customer_user1.id}/{uuid.uuid4()}.stl"
        data = {
            "design_name": "Task Trigger Test Part API", # Differentiate name
            "s3_file_key": s3_key,
            "material": "Nylon",
            "quantity": 5
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_design_id = response.data['id']
        mock_analyze_task_delay.assert_called_once_with(uuid.UUID(created_design_id))


# Celery Task Tests
import shutil # For copying sample file in tests
from pathlib import Path # For path manipulation
from .tasks import analyze_cad_file, STEPUTILS_AVAILABLE, NUMPY_STL_AVAILABLE # Import the task and availability flags
from botocore.exceptions import ClientError
from unittest import skipIf # To skip tests if libraries are not available
# from stl import mesh as stl_mesh_module # To mock its from_file method - numpy-stl is imported in tasks

# Path to the sample STL file
SAMPLE_STL_DIR = Path(__file__).parent / "test_data"
SAMPLE_STL_FILE_PATH = SAMPLE_STL_DIR / "cube_10mm.stl"
SAMPLE_STEP_FILE_PATH = SAMPLE_STL_DIR / "cube_10mm.step"
SAMPLE_BAD_STEP_FILE_PATH = SAMPLE_STL_DIR / "bad_cube.step"
SAMPLE_IGES_FILE_PATH = SAMPLE_STL_DIR / "dummy.iges"


class DesignAnalysisTaskTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Test data files should be committed to the repository.
        # This setup ensures they exist for testing.
        if not SAMPLE_STL_DIR.exists():
            SAMPLE_STL_DIR.mkdir(parents=True, exist_ok=True)
            # Simplified: assume files are present or tests requiring them will be skipped or fail informatively.

        cls.customer_user = User.objects.create_user(
            email="taskuser@example.com", password="Password123!",
            company_name="Task Test Corp", role=UserRole.CUSTOMER
        )
        cls.design_pending_stl = Design.objects.create(
            customer=cls.customer_user,
            design_name="STL Design for Task Test",
            s3_file_key=f"uploads/designs/{cls.customer_user.id}/cube_10mm.stl",
            material="PLA", quantity=1, status=DesignStatus.PENDING_ANALYSIS
        )
        cls.design_pending_step = Design.objects.create(
            customer=cls.customer_user,
            design_name="STEP Design for Task Test",
            s3_file_key=f"uploads/designs/{cls.customer_user.id}/cube_10mm.step",
            material="Steel", quantity=1, status=DesignStatus.PENDING_ANALYSIS
        )
        cls.design_pending_bad_step = Design.objects.create(
            customer=cls.customer_user,
            design_name="Bad STEP Design",
            s3_file_key=f"uploads/designs/{cls.customer_user.id}/bad_cube.step",
            material="Unknown", quantity=1, status=DesignStatus.PENDING_ANALYSIS
        )
        cls.design_pending_iges = Design.objects.create(
            customer=cls.customer_user,
            design_name="IGES Design for Task Test",
            s3_file_key=f"uploads/designs/{cls.customer_user.id}/dummy.iges",
            material="Plastic", quantity=1, status=DesignStatus.PENDING_ANALYSIS
        )
        cls.design_pending_unsupported = Design.objects.create(
            customer=cls.customer_user,
            design_name="Unsupported File Type Test",
            s3_file_key=f"uploads/designs/{cls.customer_user.id}/unsupported.txt",
            material="Paper", quantity=1, status=DesignStatus.PENDING_ANALYSIS
        )
        cls.design_processed = Design.objects.create(
            customer=cls.customer_user,
            design_name="Already Processed Design",
            s3_file_key=f"uploads/designs/{cls.customer_user.id}/processed.stl",
            material="PLA", quantity=1, status=DesignStatus.ANALYSIS_COMPLETE
        )

    def _mock_s3_download_file(self, s3_client_mock, source_file_path=SAMPLE_STL_FILE_PATH):
        """Helper to mock the S3 download_file to copy a local sample file."""
        def copier(Bucket, Key, TargetFilePath):
            shutil.copy(source_file_path, TargetFilePath)
        s3_client_mock.download_file.side_effect = copier
        return s3_client_mock

    @patch('designs.tasks.boto3.client')
    def test_analyze_cad_file_task_success_stl(self, mock_boto_client_constructor):
        mock_s3_instance = MagicMock()
        self._mock_s3_download_file(mock_s3_instance, SAMPLE_STL_FILE_PATH)
        mock_boto_client_constructor.return_value = mock_s3_instance

        result_message = analyze_cad_file(self.design_pending_stl.id)

        self.design_pending_stl.refresh_from_db()
        self.assertEqual(self.design_pending_stl.status, DesignStatus.ANALYSIS_COMPLETE)
        geom_data = self.design_pending_stl.geometric_data
        self.assertIsNotNone(geom_data)

        # Expected values for a 10x10x10 mm cube
        self.assertAlmostEqual(geom_data.get("volume_cm3"), 1.0, places=2) # 1000 mm^3 = 1 cm^3
        bbox = geom_data.get("bbox_mm", [])
        self.assertEqual(len(bbox), 3)
        for dim in bbox: self.assertAlmostEqual(dim, 10.0, places=1)
        self.assertAlmostEqual(geom_data.get("surface_area_cm2"), 6.0, places=2) # 600 mm^2 = 6 cm^2
        self.assertEqual(geom_data.get("num_triangles"), 12)
        self.assertAlmostEqual(geom_data.get("complexity_score"), 0.0012, places=4)
        self.assertTrue(geom_data.get("analysis_engine", "").startswith("numpy-stl"))
        self.assertIn("Successfully processed", result_message)
        mock_s3_instance.download_file.assert_called_once()

    @patch('designs.tasks.boto3.client')
    def test_analyze_cad_file_task_s3_download_404(self, mock_boto_client_constructor):
        mock_s3_instance = MagicMock()
        mock_s3_instance.download_file.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'download_file'
        )
        mock_boto_client_constructor.return_value = mock_s3_instance

        result_message = analyze_cad_file(self.design_pending_stl.id)

        self.design_pending_stl.refresh_from_db()
        self.assertEqual(self.design_pending_stl.status, DesignStatus.ANALYSIS_FAILED)
        self.assertIn("error", self.design_pending_stl.geometric_data)
        self.assertIn("S3 file not found", self.design_pending_stl.geometric_data["error"])
        self.assertIn("S3 file not found", result_message)

    @patch('designs.tasks.boto3.client')
    @patch('designs.tasks.stl_mesh.Mesh.from_file') # Patch the from_file method of numpy-stl
    def test_analyze_cad_file_task_stl_parsing_error(self, mock_stl_from_file, mock_boto_client_constructor):
        mock_s3_instance = MagicMock()
        self._mock_s3_download_file(mock_s3_instance, SAMPLE_STL_FILE_PATH) # Download will "succeed"
        mock_boto_client_constructor.return_value = mock_s3_instance

        mock_stl_from_file.side_effect = ValueError("Simulated STL parsing error")

        analyze_cad_file(self.design_pending_stl.id)

        self.design_pending_stl.refresh_from_db()
        self.assertEqual(self.design_pending_stl.status, DesignStatus.ANALYSIS_FAILED)
        self.assertIn("error", self.design_pending_stl.geometric_data)
        self.assertIn("Analysis failed: Invalid or corrupt STL file", self.design_pending_stl.geometric_data["error"])

    @patch('designs.tasks.boto3.client')
    def test_analyze_cad_file_task_unsupported_file_type(self, mock_boto_client_constructor):
        mock_s3_instance = MagicMock()
        # Create a dummy .txt file for download simulation
        # For this test, the content doesn't matter as much as the extension check.
        # We can simulate the download of a file named 'unsupported.txt'.
        # The S3 key in self.design_pending_unsupported already has .txt extension.
        self._mock_s3_download_file(mock_s3_instance, SAMPLE_STL_FILE_PATH) # Content doesn't matter, path is just placeholder
        mock_boto_client_constructor.return_value = mock_s3_instance

        analyze_cad_file(self.design_pending_unsupported.id)

        self.design_pending_unsupported.refresh_from_db()
        self.assertEqual(self.design_pending_unsupported.status, DesignStatus.ANALYSIS_FAILED)
        self.assertIn("error", self.design_pending_unsupported.geometric_data)
        self.assertIn("Unsupported file type: .txt", self.design_pending_unsupported.geometric_data["error"])

    def test_analyze_cad_file_task_design_not_found(self):
        non_existent_uuid = uuid.uuid4()
        result_message = analyze_cad_file(non_existent_uuid)
        self.assertIn(f"Failed: Design {non_existent_uuid} not found", result_message)

    def test_analyze_cad_file_task_already_processed(self):
        result_message = analyze_cad_file(self.design_processed.id)
        self.assertIn(f"Skipped: Design {self.design_processed.id} not in PENDING_ANALYSIS status", result_message)
        self.design_processed.refresh_from_db()
        self.assertEqual(self.design_processed.status, DesignStatus.ANALYSIS_COMPLETE)
            email="taskuser@example.com", password="Password123!",
            company_name="Task Test Corp", role=UserRole.CUSTOMER
        )
        self.design_pending = Design.objects.create(
            customer=self.customer_user,
            design_name="Design for Task Test",
            s3_file_key=f"uploads/designs/{self.customer_user.id}/task_test.stl",
            material="ABS", quantity=1, status=DesignStatus.PENDING_ANALYSIS
        )
        self.design_processed = Design.objects.create(
            customer=self.customer_user,
            design_name="Already Processed Design",
            s3_file_key=f"uploads/designs/{self.customer_user.id}/processed.stl",
            material="PLA", quantity=1, status=DesignStatus.ANALYSIS_COMPLETE
        )

    @patch('designs.tasks.boto3.client') # Patch where boto3.client is used in tasks.py
    @patch('designs.tasks.mock_cad_analysis') # Patch our mock CAD analysis function
    def test_analyze_cad_file_task_success(self, mock_analysis_func, mock_boto_client_constructor):
        # Configure mock S3 client
        mock_s3_instance = MagicMock()
        mock_boto_client_constructor.return_value = mock_s3_instance

        # Configure mock CAD analysis results
        mock_analysis_results = {
            "volume_cm3": 100.0, "bbox_mm": [10,20,30],
            "surface_area_cm2": 600.0, "complexity_score": 0.5,
            "analysis_engine": "mock_engine_v1.0_test"
        }
        mock_analysis_func.return_value = mock_analysis_results

        # Run the task directly for testing (synchronously)
        result_message = analyze_cad_file(self.design_pending.id)

        self.design_pending.refresh_from_db()
        self.assertEqual(self.design_pending.status, DesignStatus.ANALYSIS_COMPLETE)
        self.assertEqual(self.design_pending.geometric_data, mock_analysis_results)
        self.assertIn("Successfully processed", result_message)

        mock_s3_instance.download_file.assert_called_once()
        # args, kwargs = mock_s3_instance.download_file.call_args
        # self.assertEqual(args[0], settings.AWS_STORAGE_BUCKET_NAME)
        # self.assertEqual(args[1], self.design_pending.s3_file_key)

        mock_analysis_func.assert_called_once()


    @patch('designs.tasks.boto3.client')
    @patch('designs.tasks.mock_cad_analysis') # Still need to patch it even if not called due to S3 error
    def test_analyze_cad_file_task_s3_download_404(self, mock_analysis_func, mock_boto_client_constructor):
        mock_s3_instance = MagicMock()
        # Simulate S3 404 error
        mock_s3_instance.download_file.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'download_file'
        )
        mock_boto_client_constructor.return_value = mock_s3_instance

        result_message = analyze_cad_file(self.design_pending.id)

        self.design_pending.refresh_from_db()
        self.assertEqual(self.design_pending.status, DesignStatus.ANALYSIS_FAILED)
        self.assertIn("error", self.design_pending.geometric_data)
        self.assertIn("S3 file not found", self.design_pending.geometric_data["error"])
        self.assertIn("S3 file not found", result_message)
        mock_analysis_func.assert_not_called() # Analysis should not run if download fails

    @patch('designs.tasks.boto3.client')
    @patch('designs.tasks.mock_cad_analysis')
    def test_analyze_cad_file_task_analysis_failure(self, mock_analysis_func, mock_boto_client_constructor):
        mock_s3_instance = MagicMock() # S3 download is successful
        mock_boto_client_constructor.return_value = mock_s3_instance

        # Simulate failure in the (mocked) CAD analysis step
        mock_analysis_func.side_effect = ValueError("Simulated CAD processing error")

        analyze_cad_file(self.design_pending.id)

        self.design_pending.refresh_from_db()
        self.assertEqual(self.design_pending.status, DesignStatus.ANALYSIS_FAILED)
        self.assertIn("error", self.design_pending.geometric_data)
        self.assertIn("Analysis failed: Simulated CAD processing error", self.design_pending.geometric_data["error"])

    def test_analyze_cad_file_task_design_not_found(self):
        non_existent_uuid = uuid.uuid4()
        result_message = analyze_cad_file(non_existent_uuid)
        self.assertIn(f"Failed: Design {non_existent_uuid} not found", result_message)

    def test_analyze_cad_file_task_already_processed(self):
        result_message = analyze_cad_file(self.design_processed.id)
        self.assertIn(f"Skipped: Design {self.design_processed.id} not in PENDING_ANALYSIS status", result_message)
        self.design_processed.refresh_from_db()
        # Ensure status and data haven't changed
        self.assertEqual(self.design_processed.status, DesignStatus.ANALYSIS_COMPLETE)


# --- Test GenerateQuotesView API Endpoint ---
class GenerateQuotesViewTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="quotegen_cust@example.com", password="password", role=UserRole.CUSTOMER
        )
        self.admin_user = User.objects.create_superuser(
            email="quotegen_admin@example.com", password="password", company_name="AdminQuote"
        )
        self.manufacturer1_user = User.objects.create_user(
            email="quotegen_mf1@example.com", password="password", role=UserRole.MANUFACTURER, company_name="MF1 Pricing"
        )
        self.manufacturer1_profile = Manufacturer.objects.create(
            user=self.manufacturer1_user,
            markup_factor="1.20",
            capabilities={
                "materials_supported": ["PLA", "ABS"], # MF1 supports PLA and ABS
                "max_size_mm": [200, 200, 200],       # MF1 can handle large parts
                "pricing_factors": {
                    "material_properties": {
                        "PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 20.0},
                        "ABS": {"density_g_cm3": 1.04, "cost_usd_kg": 25.0}
                    },
                    "machining": {"base_time_cost_unit": "10.0", "time_multiplier_complexity_cost_unit": "50.0"},
                    "estimated_lead_time_base_days": 5
                }
            }
        )
        self.manufacturer2_user = User.objects.create_user(
            email="quotegen_mf2@example.com", password="password", role=UserRole.MANUFACTURER, company_name="MF2 Pricing"
        )
        self.manufacturer2_profile = Manufacturer.objects.create(
            user=self.manufacturer2_user,
            markup_factor="1.30",
            capabilities={
                "materials_supported": ["PLA"],             # MF2 only supports PLA
                "max_size_mm": [150, 150, 150],
                "pricing_factors": {
                    "material_properties": {"PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 18.0}},
                    "machining": {"base_time_cost_unit": "12.0", "time_multiplier_complexity_cost_unit": "55.0"},
                    "estimated_lead_time_base_days": 7
                }
            }
        )

        self.design_analyzed = Design.objects.create( # Used as a base for many tests
            customer=self.customer, design_name="Design for Auto-Quote", material="ABS", quantity=1,
            status=DesignStatus.ANALYSIS_COMPLETE,
            geometric_data={"volume_cm3": 50.0, "complexity_score": 0.8, "bbox_mm": [50, 40, 30]} # Added bbox
        )
        self.design_pending = Design.objects.create(
            customer=self.customer, design_name="Design Pending for Auto-Quote", material="PLA", quantity=1,
            status=DesignStatus.PENDING_ANALYSIS
        )
        self.design_no_geom = Design.objects.create(
            customer=self.customer, design_name="Design No Geom for Auto-Quote", material="PLA", quantity=1,
            status=DesignStatus.ANALYSIS_COMPLETE, geometric_data=None # No bbox
        )

        self.manufacturer3_user = User.objects.create_user( # PLA only, CNC capable
            email="quotegen_mf3@example.com", password="password", role=UserRole.MANUFACTURER, company_name="MF3 PLA Only CNC"
        )
        self.manufacturer3_profile = Manufacturer.objects.create(
            user=self.manufacturer3_user, markup_factor="1.15",
            capabilities={
                "materials_supported": ["PLA"], "max_size_mm": [200, 200, 200], "cnc": True,
                "pricing_factors": {
                    "material_properties": {"PLA": {"density_g_cm3": 1.25, "cost_usd_kg": 15.0}},
                    "machining": {"base_time_cost_unit": "8.0", "time_multiplier_complexity_cost_unit": "40.0"},
                    "estimated_lead_time_base_days": 6
                }
            }
        )
        self.manufacturer4_user = User.objects.create_user( # ABS, small, explicitly NO CNC
            email="quotegen_mf4@example.com", password="password", role=UserRole.MANUFACTURER, company_name="MF4 ABS Small NoCNC"
        )
        self.manufacturer4_profile = Manufacturer.objects.create(
            user=self.manufacturer4_user, markup_factor="1.22",
            capabilities={
                "materials_supported": ["ABS"], "max_size_mm": [50, 50, 50], "cnc": False,
                "pricing_factors": {
                    "material_properties": {"ABS": {"density_g_cm3": 1.04, "cost_usd_kg": 28.0}},
                    "machining": {"base_time_cost_unit": "15.0", "time_multiplier_complexity_cost_unit": "60.0"},
                     "estimated_lead_time_base_days": 8 # Added for completeness
                }
            }
        )
        # Update MF1 to be CNC capable for tests
        self.manufacturer1_profile.capabilities["cnc"] = True
        self.manufacturer1_profile.save()

        # Update MF2 capabilities for some tests (PLA, no CNC specified, should pass CNC filter by default)
        self.manufacturer2_profile.capabilities["max_size_mm"] = [150,150,150] # Ensure size for some tests
        self.manufacturer2_profile.save()


    def _login(self, user_obj):
        self.client.force_authenticate(user=user_obj)

    def test_generate_quotes_success(self):
        self._login(self.customer) # Design owner triggers
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("generated_quotes", response.data)
        # MF1 and MF4 should be able to quote this ABS design.
        self.assertEqual(len(response.data["generated_quotes"]), 2)
        self.assertEqual(response.data["message"], f"2 quote(s) generated successfully for design '{self.design_analyzed.design_name}'.")

        self.design_analyzed.refresh_from_db()
        self.assertEqual(self.design_analyzed.status, DesignStatus.QUOTED)

        # Verify quotes from MF1 and MF4
        mf_ids_who_quoted = {q['manufacturer'] for q in response.data['generated_quotes']} # q['manufacturer'] is already a UUID
        self.assertIn(self.manufacturer1_user.id, mf_ids_who_quoted)
        self.assertIn(self.manufacturer4_user.id, mf_ids_who_quoted)

        # Optional: Check specific price for one of them if needed, e.g. MF1
        quote_mf1 = Quote.objects.get(design=self.design_analyzed, manufacturer=self.manufacturer1_user)
        # Expected for MF1: MatCost = 50*1.04*(25/1000) = 1.3. MachineCost = 10 + (0.8*50) = 50. TotalBeforeMarkup = 51.3. Total = 51.3*1.2 = 61.56
        self.assertEqual(float(quote_mf1.price_usd), 61.56)
        self.assertEqual(quote_mf1.estimated_lead_time_days, 5)

    def test_generate_quotes_design_not_analyzed(self):
        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_pending.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(f"Design must be in '{DesignStatus.ANALYSIS_COMPLETE.label}' status", response.data['error'])

    def test_generate_quotes_design_no_geometric_data(self):
        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_no_geom.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Design geometric data is missing", response.data['error'])

    def test_generate_quotes_unauthorized_user(self):
        other_customer = User.objects.create_user(email="other@example.com", password="pw", role=UserRole.CUSTOMER)
        self._login(other_customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # IsOwnerOrAdmin permission

    def test_generate_quotes_manufacturer_is_owner(self):
        # Create design owned by manufacturer1_user
        mf1_design = Design.objects.create(
            customer=self.manufacturer1_user, design_name="MF1 Owned Design", material="PLA", quantity=1,
            status=DesignStatus.ANALYSIS_COMPLETE,
            geometric_data={"volume_cm3": 10.0, "complexity_score": 0.2}
        )
        self._login(self.manufacturer1_user) # Logged in as owner
        url = reverse('design_generate_quotes', kwargs={'id': mf1_design.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # Design is PLA. MF1 (owner) skipped.
        # MF2 (PLA, size [150,150,150]) - should quote for bbox [10,10,10].
        # MF3 (PLA, size [200,200,200]) - should quote.
        # MF4 (ABS only) - skipped.
        self.assertEqual(len(response.data["generated_quotes"]), 2)
        generated_quote_mf_ids = {q['manufacturer'] for q in response.data["generated_quotes"]} # q['manufacturer'] is already a UUID
        self.assertIn(self.manufacturer2_user.id, generated_quote_mf_ids)
        self.assertIn(self.manufacturer3_user.id, generated_quote_mf_ids)
        self.assertNotIn(self.manufacturer1_user.id, generated_quote_mf_ids) # Owner
        self.assertNotIn(self.manufacturer4_user.id, generated_quote_mf_ids) # Wrong material


    def test_generate_quotes_manufacturer_already_quoted(self):
        self._login(self.customer)
        # MF1 manually quotes first
        Quote.objects.create(
            design=self.design_analyzed, manufacturer=self.manufacturer1_user,
            price_usd="100.00", estimated_lead_time_days=10
        )
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')

        # MF1 already quoted. MF2 cannot make ABS, so its pricing will fail.
        # Thus, 0 new quotes generated, and there's an error for MF2.
        # MF1 already quoted. MF2 (PLA only) & MF3 (PLA only) cannot quote ABS. MF4 (ABS, size [50,50,50]) can.
        # So, 1 new quote from MF4 is expected.
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data.get("generated_quotes", [])), 1)
        self.assertEqual(response.data["generated_quotes"][0]['manufacturer'], self.manufacturer4_user.id)
        self.assertIn("1 quote(s) generated successfully", response.data["message"])

        self.design_analyzed.refresh_from_db()
        # Status should change to QUOTED as one new quote was made.
        self.assertEqual(self.design_analyzed.status, DesignStatus.QUOTED)

    def test_generate_quotes_pricing_errors_for_some_manufacturers(self):
        # Design is ABS. Bbox is [50,40,30] from self.design_analyzed.
        # MF1: Supports ABS, size [200,200,200]. We make its ABS pricing invalid (missing density).
        # MF2: PLA only. Skipped.
        # MF3: PLA only. Skipped.
        # MF4: Supports ABS, size [50,50,50]. To ensure this test results in 400 (no quotes),
        #      we must ensure MF4 also cannot quote. Let's make the design too big for MF4 for this test.

        original_design_geom = self.design_analyzed.geometric_data
        self.design_analyzed.geometric_data = {"volume_cm3": 150.0, "complexity_score": 0.9, "bbox_mm": [60, 50, 50]} # Too big for MF4
        self.design_analyzed.save()

        # Make MF1's ABS pricing data invalid
        mf1_caps = self.manufacturer1_profile.capabilities
        mf1_caps['pricing_factors']['material_properties']['ABS'] = {"cost_usd_kg": 25.0} # Missing density
        self.manufacturer1_profile.capabilities = mf1_caps
        self.manufacturer1_profile.save()

        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIn("errors_by_manufacturer", response.data)
        self.assertIn(str(self.manufacturer1_user.id), response.data["errors_by_manufacturer"]) # MF1 has pricing error
        self.assertTrue(any("Density for material 'ABS' must be positive." in e for e in response.data["errors_by_manufacturer"][str(self.manufacturer1_user.id)]))
        # MF2, MF3 are skipped by material. MF4 is skipped by size. So no errors reported for them, just no quotes.
        self.assertNotIn(str(self.manufacturer2_user.id), response.data["errors_by_manufacturer"])
        self.assertNotIn(str(self.manufacturer4_user.id), response.data["errors_by_manufacturer"])
        self.assertEqual(Quote.objects.filter(design=self.design_analyzed).count(), 0)

        self.design_analyzed.refresh_from_db()
        self.assertEqual(self.design_analyzed.status, DesignStatus.ANALYSIS_COMPLETE)

        # Restore original geometry for other tests if necessary, though test DB is reset per test method.
        # self.design_analyzed.geometric_data = original_design_geom
        # self.design_analyzed.save()

    def test_generate_quotes_filter_by_material(self):
        # self.design_analyzed is "ABS". MF1 & MF4 support ABS. MF2 & MF3 support PLA.
        # MF4 is too small. So only MF1 should quote.
        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # self.design_analyzed is "ABS". MF1 and MF4 support ABS and should fit.
        self.assertEqual(len(response.data["generated_quotes"]), 2)
        manufacturer_ids_quoted = {q['manufacturer'] for q in response.data["generated_quotes"]} # q['manufacturer'] is already a UUID
        self.assertIn(self.manufacturer1_user.id, manufacturer_ids_quoted)
        self.assertIn(self.manufacturer4_user.id, manufacturer_ids_quoted)

    def test_generate_quotes_filter_by_size(self):
        # Design: material="ABS", bbox will be [50,50,50] effectively from geometric_data for design_analyzed
        # (assuming geometric_data.bbox_mm = [X,Y,Z] are actual dimensions here for simplicity, sorted later)
        # MF1: supports ABS, size is assumed large enough from default capabilities (not explicitly set in test yet)
        # MF4: supports ABS, size [50,50,50] - should fit if design bbox is e.g. [40,40,40]
        # Let's update design_analyzed bbox for this test and MF1 capabilities for size.

        self.design_analyzed.geometric_data = {"volume_cm3": 50.0, "complexity_score": 0.8, "bbox_mm": [40, 40, 40]}
        self.design_analyzed.save()

        self.manufacturer1_profile.capabilities["max_size_mm"] = [100, 100, 100] # MF1 can handle it
        self.manufacturer1_profile.save()

        # MF4 has max_size_mm = [50, 50, 50], so it can also handle [40,40,40]

        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["generated_quotes"]), 2) # Both MF1 and MF4 should quote
        manufacturer_ids_quoted = {q['manufacturer'] for q in response.data["generated_quotes"]}
        self.assertIn(self.manufacturer1_user.id, manufacturer_ids_quoted)
        self.assertIn(self.manufacturer4_user.id, manufacturer_ids_quoted)

    def test_generate_quotes_filter_by_size_too_large(self):
        self.design_analyzed.geometric_data = {"volume_cm3": 150.0, "complexity_score": 0.9, "bbox_mm": [60, 60, 60]}
        self.design_analyzed.save() # This design is too large for MF4 ([50,50,50])

        self.manufacturer1_profile.capabilities["max_size_mm"] = [100, 100, 100] # MF1 can handle
        self.manufacturer1_profile.save()

        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["generated_quotes"]), 1) # Only MF1 quotes
        self.assertEqual(response.data["generated_quotes"][0]['manufacturer'], self.manufacturer1_user.id)

    def test_generate_quotes_no_eligible_manufacturers(self):
        self.design_analyzed.material = "ExoticAlloy" # No one supports this
        self.design_analyzed.geometric_data = {"volume_cm3": 10.0, "complexity_score": 0.1, "bbox_mm": [10,10,10]}
        self.design_analyzed.save()

        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data) # View returns 200 with message
        self.assertEqual(len(response.data.get("generated_quotes", [])), 0)
        self.assertIn("No manufacturers found matching", response.data["message"])

    def test_generate_quotes_filter_by_cnc_capability(self):
        # Design is ABS, bbox [50,40,30].
        # MF1: ABS, size [200,200,200], cnc: True -> Should quote
        # MF4: ABS, size [50,50,50], cnc: False -> Should be skipped by CNC filter
        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': self.design_analyzed.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data["generated_quotes"]), 1)
        self.assertEqual(response.data["generated_quotes"][0]['manufacturer'], self.manufacturer1_user.id)

    def test_generate_quotes_filter_size_permutation_fits(self):
        # Design bbox: 10x100x10 (sorted: 10,10,100)
        # MF_A max_size_mm: 100x100x20 (sorted: 20,100,100)
        # Permutation 10x10x100 fits 20x100x100.
        design_perm_fit = Design.objects.create(
            customer=self.customer, design_name="Permutation Fit Design", material="PLA", quantity=1,
            status=DesignStatus.ANALYSIS_COMPLETE,
            geometric_data={"volume_cm3": 10000.0, "complexity_score": 0.1, "bbox_mm": [10, 100, 10]}
        )
        # MF2 supports PLA, max_size [150,150,150] (sorted) - this design fits.
        # MF3 supports PLA, max_size [200,200,200] (sorted) - this design fits.

        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': design_perm_fit.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # MF1 (ABS, CNC=T), MF4(ABS, CNC=F) filtered by material.
        # MF2 (PLA, no CNC specified -> passes CNC filter, size [150,150,150]) - should quote.
        # MF3 (PLA, CNC=T, size [200,200,200]) - should quote.
        self.assertEqual(len(response.data["generated_quotes"]), 2)
        quoted_mf_ids = {q['manufacturer'] for q in response.data["generated_quotes"]}
        self.assertIn(self.manufacturer2_user.id, quoted_mf_ids)
        self.assertIn(self.manufacturer3_user.id, quoted_mf_ids)


    def test_generate_quotes_filter_size_permutation_does_not_fit(self):
        # Design bbox: 10x120x120 (sorted: 10,120,120)
        # MF_A max_size_mm: 100x100x100 (sorted: 100,100,100) - No permutation fits.
        design_perm_no_fit = Design.objects.create(
            customer=self.customer, design_name="Permutation NoFit Design", material="PLA", quantity=1,
            status=DesignStatus.ANALYSIS_COMPLETE,
            geometric_data={"volume_cm3": 10.0, "complexity_score": 0.1, "bbox_mm": [10, 120, 120]}
        )
        # Update MF2 to have max_size [100,100,100]
        self.manufacturer2_profile.capabilities["max_size_mm"] = [100,100,100]
        self.manufacturer2_profile.save()
        # MF3 still has [200,200,200] so it will fit.

        self._login(self.customer)
        url = reverse('design_generate_quotes', kwargs={'id': design_perm_no_fit.id})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        # MF1 (ABS), MF4(ABS) - filtered by material.
        # MF2 (PLA, size [100,100,100]) - should NOT quote.
        # MF3 (PLA, size [200,200,200]) - should quote.
        self.assertEqual(len(response.data["generated_quotes"]), 1)
        self.assertEqual(response.data["generated_quotes"][0]['manufacturer'], self.manufacturer3_user.id)
