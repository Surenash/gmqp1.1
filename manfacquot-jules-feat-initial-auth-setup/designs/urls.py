from django.urls import path, include # Added include
from . import views # Changed to import all views from the app

# Import the specific list from quotes.urls first
from quotes.urls import design_specific_quote_urlpatterns as design_specific_quote_urlpatterns_from_quotes_app

# URLs for /api/designs/
urlpatterns = [
    # POST /api/designs/upload-url - Get pre-signed S3 URL
    path('upload-url', views.DesignUploadURLView.as_view(), name='design_upload_url'),

    # POST /api/designs/ - Create a new Design record (after S3 upload)
    # GET  /api/designs/ - List Designs for the authenticated customer
    path('', views.DesignListCreateView.as_view(), name='design_list_create'),

    # GET    /api/designs/<uuid:id>/ - Retrieve a specific Design
    # PUT    /api/designs/<uuid:id>/ - Update a specific Design
    # PATCH  /api/designs/<uuid:id>/ - Partially update a specific Design
    # DELETE /api/designs/<uuid:id>/ - Delete a specific Design
    path('<uuid:id>', views.DesignDetailView.as_view(), name='design_detail'),

    # Nested quotes for a design: /api/designs/<uuid:design_id>/quotes/
    path('<uuid:design_id>/quotes/', include(design_specific_quote_urlpatterns_from_quotes_app)), # design_id will be used by QuoteListCreateView

    # Automated quote generation for a specific design
    # The view name is GenerateQuotesView, design ID is 'id' in its post method
    path('<uuid:id>/generate-quotes', views.GenerateQuotesView.as_view(), name='design_generate_quotes'),
]
