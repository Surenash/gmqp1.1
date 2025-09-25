from django.urls import path
from .views import QuoteListCreateView, QuoteDetailView

# Base for these URLs will likely be /api/
# URLs related to quotes.
# It's common to nest quote creation under designs.
# e.g., /api/designs/{design_id}/quotes/ (for list/create)
# and /api/quotes/{quote_id}/ (for detail/update/delete)

urlpatterns = [
    # Specific quote operations by quote ID
    path('<uuid:id>', QuoteDetailView.as_view(), name='quote_detail'),
    # List/Create will be handled by a URL possibly in designs.urls or a rooter setup
    # For now, this file will only contain the detail view.
    # The ListCreate view will be nested under designs.
]

# It's often better to define the ListCreate path in the app that "owns" the parent resource.
# So, /api/designs/{design_id}/quotes/ would be in designs/urls.py.
# However, if we want a flat /api/quotes/ for POST (with design_id in payload), it could be here.
# Given the views, QuoteListCreateView expects design_id from URL kwargs.

# Let's define a separate list for URLs that might be included by other apps (like designs)
# This is a common pattern for nested resources.
design_specific_quote_urlpatterns = [
    path('', QuoteListCreateView.as_view(), name='design_quote_list_create'),
]
