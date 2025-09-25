import logging
import uuid
import boto3 # Ensure boto3 is installed
from botocore.exceptions import ClientError
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
# from accounts.models import UserRole # If needed for role checks, though IsAuthenticated is primary here

logger = logging.getLogger(__name__)

class DesignUploadURLView(APIView):
    """
    Generates a pre-signed S3 URL for uploading a design file.
    POST /api/designs/upload-url
    Request Body: { "fileName": "part_v1.stl", "fileType": "model/stl" }
    Response: { "uploadUrl": "...", "s3Key": "..." }
    """
    permission_classes = [IsAuthenticated] # Only authenticated users (customers) can get an upload URL

    # Optional: Add role check if only 'customer' role should upload
    # def check_permissions(self, request):
    #     super().check_permissions(request)
    #     if request.user.role != UserRole.CUSTOMER:
    #         self.permission_denied(
    #             request, message="Only customers can upload designs."
    #         )

    def post(self, request, *args, **kwargs):
        file_name = request.data.get('fileName')
        file_type = request.data.get('fileType') # e.g., 'model/stl', 'application/step'

        if not file_name:
            return Response({"error": "fileName is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Basic validation for file_type (can be expanded)
        # Spec mentions STL, STEP, IGES. Common MIME types:
        # STL: model/stl, model/x.stl-ascii, model/x.stl-binary
        # STEP: application/step, application/STEP, application/x-step
        # IGES: model/iges
        # For simplicity, we might rely on the client sending a reasonable ContentType
        # or enforce a few common ones.

        # Sanitize file_name to prevent issues, or use a UUID for the actual S3 object name part
        original_file_name_parts = file_name.split('.')
        file_extension = original_file_name_parts[-1] if len(original_file_name_parts) > 1 else ''

        # Create a unique S3 key: prefix/user_id/uuid.extension
        s3_object_name = f"{settings.AWS_S3_DESIGNS_UPLOAD_PREFIX.strip('/')}/{request.user.id}/{uuid.uuid4()}.{file_extension}"

        s3_params = {
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': s3_object_name,
        }
        # Add ContentType if file_type is provided by the client.
        # The client should use this ContentType when PUTting the file to S3.
        if file_type:
            s3_params['ContentType'] = file_type

        # Forcing Content-Disposition can help if files are ever directly accessed via browser,
        # suggesting a download with the original filename.
        # s3_params['ContentDisposition'] = f'attachment; filename="{file_name}"'


        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL, # Important for LocalStack/MinIO
                config=boto3.session.Config(signature_version=settings.AWS_S3_SIGNATURE_VERSION)
            )

            presigned_url = s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params=s3_params,
                ExpiresIn=settings.AWS_S3_PRESIGNED_URL_EXPIRATION, # In seconds
                HttpMethod='PUT'
            )

            return Response({
                'uploadUrl': presigned_url,
                's3Key': s3_object_name  # The key the client should use to confirm upload later
            }, status=status.HTTP_200_OK)

        except ClientError as e:
            logger.error(f"S3 ClientError generating pre-signed URL for {s3_object_name}: {e}")
            return Response({"error": "Could not generate upload URL. S3 client error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error generating pre-signed URL for {s3_object_name}: {e}")
            # In production, avoid sending detailed internal errors to client
            return Response({"error": "An unexpected error occurred while preparing the file upload."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Design CRUD Views ---
from rest_framework import generics
from .models import Design
from .serializers import DesignSerializer, DesignCreateSerializer
from accounts.models import UserRole # For permission check

class IsOwnerOrAdmin(IsAuthenticated): # Or use DRF's IsAuthenticatedOrReadOnly for public GETs
    """
    Custom permission to only allow design owners or admin users to access/edit.
    For retrieve/update/delete. List might be different.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users can access anything
        if request.user and request.user.is_staff:
            return True
        # Owner of the design can access
        return obj.customer == request.user

class IsCustomerUser(IsAuthenticated):
    """
    Custom permission to only allow users with 'customer' role.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == UserRole.CUSTOMER

class DesignListCreateView(generics.ListCreateAPIView):
    """
    POST /api/designs - Create a new design record.
    GET /api/designs - List designs for the authenticated customer.
    """
    serializer_class = DesignSerializer # Default for list
    permission_classes = [IsAuthenticated, IsCustomerUser] # Only authenticated customers

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DesignCreateSerializer
        return DesignSerializer # For GET (list)

    def get_queryset(self):
        """
        This view should only return designs for the currently authenticated user.
        """
        user = self.request.user
        if user.is_authenticated:
            # Further check if user is customer, though IsCustomerUser permission handles this.
            # If admin/staff should see all, add logic here:
            # if user.is_staff:
            #     return Design.objects.all()
            return Design.objects.filter(customer=user)
        return Design.objects.none() # Should not happen due to IsAuthenticated

    def perform_create(self, serializer):
        """
        Pass additional context (request) to the serializer if needed,
        or directly save with the customer.
        DesignCreateSerializer handles setting the customer from context.
        """
        serializer.save() # customer is set in DesignCreateSerializer.create via context

class DesignDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/designs/{id} - Get a specific design.
    PUT /api/designs/{id} - Update a specific design (limited fields typically).
    PATCH /api/designs/{id} - Partially update a specific design.
    DELETE /api/designs/{id} - Delete a specific design.
    """
    # queryset = Design.objects.all() # Initial queryset, will be filtered by get_queryset
    serializer_class = DesignSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin] # IsOwnerOrAdmin handles object-level permission
    lookup_field = 'id' # Since Design model PK is 'id' (UUID)

    def get_queryset(self):
        """
        Filter designs so that users can only see/affect their own designs,
        unless they are staff/admin. This ensures a 404 if trying to access
        another user's design by its ID directly.
        """
        user = self.request.user
        if user.is_staff:
            return Design.objects.all() # Staff can see all designs
        # Customers can only see their own designs
        # IsOwnerOrAdmin permission will still run for object-level checks,
        # but this queryset filtering ensures 404 for non-owned objects.
        return Design.objects.filter(customer=user)

    # By default, PUT would require all fields from DesignSerializer.
    # If updates are restricted (e.g., cannot change s3_key or customer post-creation),
    # a different serializer for updates might be needed, or make fields read_only in DesignSerializer.
    # For now, DesignSerializer has many read_only fields, limiting what can be updated.
    # Deletion is allowed by IsOwnerOrAdmin.


# --- Automated Quote Generation ---
from django.shortcuts import get_object_or_404
from django.db import transaction
from accounts.models import Manufacturer # Import Manufacturer model
from quotes.models import Quote # Import Quote model
from quotes.serializers import QuoteSerializer # To serialize generated quotes
from quotes.pricing import calculate_quote_price # The pricing logic
from .models import DesignStatus as DesignModelStatus # Alias to avoid clash with DRF status

class GenerateQuotesView(APIView):
    """
    POST /api/designs/{id}/generate-quotes
    Triggers automated quote generation for a given design from all suitable manufacturers.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin] # Only design owner or admin can trigger this

    def post(self, request, id, *args, **kwargs): # 'id' is the design_id from URL
        design = get_object_or_404(Design, id=id)

        # Check object permissions using the same logic as DesignDetailView for consistency
        # This ensures the IsOwnerOrAdmin check is effectively applied before proceeding.
        # (Alternatively, could make a helper or rely on get_object_or_404 with filtered queryset)
        if not (request.user.is_staff or design.customer == request.user):
            return Response(
                {"error": "You do not have permission to generate quotes for this design."},
                status=status.HTTP_403_FORBIDDEN
            )

        if design.status != DesignModelStatus.ANALYSIS_COMPLETE:
            return Response(
                {"error": f"Design must be in '{DesignModelStatus.ANALYSIS_COMPLETE.label}' status to generate quotes. Current status: {design.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not design.geometric_data:
            return Response(
                {"error": "Design geometric data is missing. Cannot generate quotes."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Implement manufacturer filtering based on capabilities matching design requirements
        # For now, iterate over ALL manufacturers.
        # In a real system, you'd filter manufacturers who can handle the design.material, design.size (from bbox), etc.
        # manufacturers = Manufacturer.objects.select_related('user').all() # Fetch related user to avoid N+1 in pricing/serializer

        # --- Enhanced Manufacturer Filtering ---
        eligible_manufacturers = []
        all_manufacturers = Manufacturer.objects.select_related('user').all()

        design_bbox_sorted = sorted(design.geometric_data.get('bbox_mm', [0,0,0]))

        for mf_profile in all_manufacturers:
            capabilities = mf_profile.capabilities or {}

            # 1. Material Matching
            supported_materials = capabilities.get('materials_supported', [])
            if design.material not in supported_materials:
                logger.info(f"Mf {mf_profile.user.email} skipped: does not support material '{design.material}'.")
                continue

            # 2. Size Matching
            # Assumes design_bbox_sorted is [dx_sorted, dy_sorted, dz_sorted]
            # Assumes mf_max_size_sorted is [mx_sorted, my_sorted, mz_sorted]
            # This simple check requires the smallest design dim fits smallest manuf. max dim, etc.
            # A more robust check would test all 6 permutations of design bbox against manuf. max_size.
            mf_max_size = capabilities.get('max_size_mm', [0,0,0])
            if not (isinstance(mf_max_size, list) and len(mf_max_size) == 3 and all(isinstance(dim, (int, float)) for dim in mf_max_size)):
                logger.warning(f"Mf {mf_profile.user.email} skipped: invalid 'max_size_mm' format in capabilities: {mf_max_size}")
                continue

            mf_max_size_sorted = sorted(mf_max_size)

            # Check if all design dimensions are less than or equal to corresponding sorted manufacturer dimensions
            # Smallest design dim <= smallest mf dim, middle <= middle, largest <= largest.
            # This is a common simplified check for fitting without specific orientation constraints.
            # if not all(d_dim <= mf_dim for d_dim, mf_dim in zip(design_bbox_sorted, mf_max_size_sorted)):
            #     logger.info(f"Mf {mf_profile.user.email} skipped: design bbox {design_bbox_sorted} does not fit max_size {mf_max_size_sorted} (sorted comparison).")
            #     continue

            # Advanced Size Check: Check all 6 permutations of design bbox
            from itertools import permutations
            design_fits_size = False
            if len(design_bbox_sorted) == 3: # Ensure bbox has 3 dimensions
                for p_design_bbox in permutations(design_bbox_sorted):
                    if (p_design_bbox[0] <= mf_max_size_sorted[0] and
                        p_design_bbox[1] <= mf_max_size_sorted[1] and
                        p_design_bbox[2] <= mf_max_size_sorted[2]):
                        design_fits_size = True
                        break
                # A simpler check if manufacturer dimensions are not sorted (i.e. X, Y, Z are fixed slots)
                # for p_design_bbox in permutations(design.geometric_data.get('bbox_mm', [0,0,0])):
                #     if (p_design_bbox[0] <= mf_max_size[0] and
                #         p_design_bbox[1] <= mf_max_size[1] and
                #         p_design_bbox[2] <= mf_max_size[2]):
                #         design_fits_size = True
                #         break
            else: # Invalid design bbox
                logger.warning(f"Mf {mf_profile.user.email} skipped: design {design.id} has invalid bbox {design.geometric_data.get('bbox_mm')}")
                continue


            if not design_fits_size:
                logger.info(f"Mf {mf_profile.user.email} skipped: design bbox {design.geometric_data.get('bbox_mm')} does not fit max_size {mf_max_size} in any orientation (sorted comparison used).")
                continue

            # 3. Capability Flag Matching (Example: CNC)
            # Assuming design doesn't explicitly require CNC for now.
            # If a manufacturer has "cnc": true, they are considered. If "cnc": false or key missing, also considered.
            # If design *required* CNC, the logic would be:
            # if design.requires_cnc and not capabilities.get("cnc", False): # Requires Design model change
            #    logger.info(f"Mf {mf_profile.user.email} skipped: design requires CNC which is not supported.")
            #    continue
            # For this example, let's say we *prefer* CNC if available, but don't filter out if not.
            # Or, for a stricter filter demonstration:
            if capabilities.get("cnc") is False: # Explicitly false
                 logger.info(f"Mf {mf_profile.user.email} skipped: does not offer CNC (explicitly set to false).")
                 continue
            # If "cnc" is true or missing, they pass this filter. (This is just an example filter behavior)


            eligible_manufacturers.append(mf_profile)

        if not eligible_manufacturers:
            return Response(
                {"message": "No manufacturers found matching the design's material or size requirements.", "generated_quotes": [], "errors_by_manufacturer": {}},
                status=status.HTTP_200_OK # Or 400 if this is considered a client-side setup issue
            )

        generated_quotes = []
        errors_by_manufacturer = {}
        quotes_created_count = 0

        with transaction.atomic(): # Ensure all quotes are created or none if a critical error occurs
            for mf_profile in eligible_manufacturers: # Use the filtered list
                # Skip if manufacturer is the design owner
                if design.customer == mf_profile.user:
                    logger.info(f"Skipping quote generation for design {design.id} from manufacturer {mf_profile.user.email} (owner).")
                    continue

                # Skip if manufacturer has already quoted this design (to avoid duplicates if endpoint is called multiple times)
                # This might be too restrictive if quotes can be re-generated. Consider business logic.
                if Quote.objects.filter(design=design, manufacturer=mf_profile.user).exists():
                    logger.info(f"Manufacturer {mf_profile.user.email} has already quoted design {design.id}. Skipping.")
                    continue

                pricing_details = calculate_quote_price(design=design, manufacturer=mf_profile)

                if pricing_details.price_usd is not None and not pricing_details.errors:
                    try:
                        quote = Quote.objects.create(
                            design=design,
                            manufacturer=mf_profile.user, # Link to the User model instance
                            price_usd=pricing_details.price_usd,
                            estimated_lead_time_days=pricing_details.estimated_lead_time_days,
                            notes=f"Automated quote based on design analysis. Calculation details: {pricing_details.calculation_details}",
                            # status defaults to PENDING
                        )
                        generated_quotes.append(quote)
                        quotes_created_count += 1
                    except Exception as e: # Catch DB errors or other unexpected issues during Quote creation
                        logger.error(f"Error creating Quote object for design {design.id}, mf {mf_profile.user.email}: {e}")
                        errors_by_manufacturer[str(mf_profile.user.id)] = f"Error saving quote: {str(e)}"
                else:
                    logger.warning(f"Could not calculate price for design {design.id} by mf {mf_profile.user.email}. Errors: {pricing_details.errors}")
                    errors_by_manufacturer[str(mf_profile.user.id)] = pricing_details.errors

            # Update design status to QUOTED if at least one quote was generated successfully
            if quotes_created_count > 0 and design.status == DesignModelStatus.ANALYSIS_COMPLETE:
                design.status = DesignModelStatus.QUOTED
                design.save(update_fields=['status', 'updated_at'])
                logger.info(f"Design {design.id} status updated to QUOTED.")


        serialized_quotes = QuoteSerializer(generated_quotes, many=True).data
        response_data = {
            "message": f"{quotes_created_count} quote(s) generated successfully for design '{design.design_name}'.",
            "generated_quotes": serialized_quotes,
        }
        if errors_by_manufacturer:
            response_data["errors_by_manufacturer"] = errors_by_manufacturer
            # Consider if a partial success (some quotes generated, some failed) is 200 OK or 207 Multi-Status
            # For now, if any quotes are made, return 200 with error details.
            # If NO quotes could be made and there were errors, maybe return 400 or 500.
            if quotes_created_count == 0:
                 return Response({
                    "message": "No quotes could be generated.",
                    "errors_by_manufacturer": errors_by_manufacturer
                 }, status=status.HTTP_400_BAD_REQUEST)


        return Response(response_data, status=status.HTTP_200_OK)
