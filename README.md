# GMQP - Global Manufacturing Quotation Platform

visit 
https://app-gg-v1-1-554903121010.us-west1.run.app
https://app-gg-v1-1-tams626wua-uw.a.run.app

This project is a web-based platform to automate the process of obtaining manufacturing quotes for custom designs.

## Technical Overview

*   **Backend:** Python 3.11 with Django 4.x (target, actual may vary by environment)
*   **Frontend:** (To be developed) React 18 with TypeScript
*   **Database:** PostgreSQL 15 (using SQLite for local development initially)
*   **API:** RESTful, using Django Rest Framework
*   **Authentication:** JWT (JSON Web Tokens) via djangorestframework-simplejwt
*   **Async Tasks:** Celery with Redis (to be implemented)
*   **File Storage:** Amazon S3 (to be implemented)
*   **Deployment:** Docker, AWS (to be implemented)

## Current Status

*   Basic Django project structure set up.
*   User registration (`/api/auth/register`) and login (`/api/auth/token`) implemented.
    *   Users have roles: `customer` or `manufacturer`.
    *   JWTs include `email`, `role`, and `company_name` claims.

## Getting Started (Local Development)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd gmqp-platform
    ```

2.  **Set up a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `requirements.txt` will be generated soon)*

4.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Create a superuser (optional, for admin panel access):**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
    The API will be accessible at `http://127.0.0.1:8000/`.

## API Endpoints Implemented

*   `POST /api/auth/register`: Register a new user.
    *   Payload: `{ "email": "user@example.com", "password": "yourpassword", "password2": "yourpassword", "company_name": "Your Company", "role": "customer" }` (role can be 'customer' or 'manufacturer')
*   `POST /api/auth/token`: Obtain JWT access and refresh tokens.
    *   Payload: `{ "email": "user@example.com", "password": "yourpassword" }`
*   `POST /api/auth/token/refresh`: Refresh an access token.
    *   Payload: `{ "refresh": "your_refresh_token" }`
*   `GET /api/auth/me`: Get current authenticated user's details (requires Bearer token).

### Manufacturer Endpoints
*   `GET /api/manufacturers/`: Get a list of all manufacturers (public).
*   `GET /api/manufacturers/{user_id}/`: Get the detailed public profile for a specific manufacturer (public).
*   `GET /api/manufacturers/profile/`: (Protected: Manufacturer Role) Get the logged-in manufacturer's own profile.
*   `PUT /api/manufacturers/profile/`: (Protected: Manufacturer Role) Update the logged-in manufacturer's own profile.
    *   Payload: `{ "location": "New Location", "markup_factor": "1.25", "capabilities": {"cnc": true, "materials_supported": ["ABS", "PLA"], "max_size_mm": [200,200,150], "pricing_factors": { ... }}, "certifications": ["ISO9001"], "website_url": "http://example.com" }` (all fields optional for partial update with PATCH).
        *   `materials_supported`: List of material names (strings).
        *   `max_size_mm`: List of 3 numbers [X, Y, Z] for max build volume.
        *   See `accounts/serializers.py` `ManufacturerProfileSerializer.validate_capabilities` for example `pricing_factors` structure.
*   `PATCH /api/manufacturers/profile/`: (Protected: Manufacturer Role) Partially update the logged-in manufacturer's own profile.

### Design Endpoints & File Upload
The process for uploading a design involves two steps:
1.  **Request an upload URL:**
    *   `POST /api/designs/upload-url`: (Protected: Customer Role) Get a pre-signed S3 URL for file upload.
        *   Request Body: `{ "fileName": "part_v1.stl", "fileType": "model/stl" }`
        *   Response: `{ "uploadUrl": "s3-presigned-url", "s3Key": "path/to/file/in/bucket.stl" }`
2.  **Upload the file:** The client uses the `uploadUrl` to PUT the file directly to S3.
3.  **Create the Design record:** After successful S3 upload, the client creates the design record in the database.
    *   `POST /api/designs/`: (Protected: Customer Role) Create a new design record.
        *   Payload: `{ "design_name": "My Awesome Part", "s3_file_key": "path/to/file/in/bucket.stl", "material": "ABS", "quantity": 100 }`
        *   Response: The created design object, including its `id` and initial `status` ('pending_analysis').
    *   Upon creation, a background task (`analyze_cad_file` Celery task) is triggered.
        *   For `.stl` files, it uses `numpy-stl` to extract volume (cm³), bounding box (mm), surface area (cm²), number of triangles, and a heuristic complexity score. These are stored in `geometric_data`.
        *   For `.step`/`.stp` files, `steputils` is used for basic validation. If valid, `geometric_data` will note successful validation but state that detailed metrics (volume, bbox, area) are not extracted. Status will be `analysis_failed` for quoting purposes if detailed metrics are missing.
        *   `.iges`/`.igs` files are currently not supported for detailed analysis and will result in `analysis_failed`.
        *   The design's `status` will update to `analysis_complete` (for STL with metrics) or `analysis_failed`.

*   `GET /api/designs/`: (Protected: Customer Role) Get a list of designs for the authenticated customer.
*   `GET /api/designs/{design_id}/`: (Protected: Owner or Admin) Get the details of a specific design.
*   `PATCH /api/designs/{design_id}/`: (Protected: Owner or Admin) Partially update a design (e.g., name, quantity - other fields like `s3_file_key` or `status` are typically backend-managed post-creation).
*   `DELETE /api/designs/{design_id}/`: (Protected: Owner or Admin) Delete a design.
*   `POST /api/designs/{design_id}/generate-quotes/`: (Protected: Design Owner or Admin) Triggers automated quote generation for the design.
    *   Manufacturers are filtered by:
        *   Material compatibility (`design.material` vs `manufacturer.capabilities.materials_supported`).
        *   Size: Design's bounding box (`geometric_data.bbox_mm`) must fit within `manufacturer.capabilities.max_size_mm` (checks all 6 orientations of design bbox against sorted manufacturer max dimensions).
        *   CNC capability (example filter: skips if manufacturer has `capabilities.cnc` set to `false`).

### Quote Endpoints
*   `POST /api/designs/{design_id}/quotes/`: (Protected: Manufacturer Role) Create a quote manually for a specific design.
    *   Payload: `{ "price_usd": "100.50", "estimated_lead_time_days": 14, "notes": "Optional notes." }`
*   `GET /api/designs/{design_id}/quotes/`: (Protected: Design Owner or Quoting Manufacturer) List quotes for a specific design.
*   `GET /api/quotes/{quote_id}/`: (Protected: Design Owner or Quoting Manufacturer) Retrieve a specific quote.
*   `PATCH /api/quotes/{quote_id}/`: (Protected: Role-dependent) Update a quote.
    *   Customers can update `status` to 'accepted' or 'rejected' if current status is 'pending'.
    *   Manufacturers can update price/lead time/notes if status is 'pending'.
    *   Payload example: `{ "status": "accepted" }` or `{ "price_usd": "95.00" }`
*   `DELETE /api/quotes/{quote_id}/`: (Protected: Manufacturer who created the quote, if status is 'pending', or Admin) Delete a quote.

### Review Endpoints
*   `POST /api/manufacturers/{manufacturer_id}/reviews/`: (Protected: Customer Role) Create a review for a specific manufacturer.
    *   Payload: `{ "rating": 5, "comment": "Great service!", "order_id": "optional-uuid-of-order" }`
*   `GET /api/manufacturers/{manufacturer_id}/reviews/`: (Public) List reviews for a specific manufacturer.
*   `GET /api/reviews/{review_id}/`: (Public) Retrieve a specific review.
*   `PATCH /api/reviews/{review_id}/`: (Protected: Review Owner or Admin) Update a review.
*   `DELETE /api/reviews/{review_id}/`: (Protected: Review Owner or Admin) Delete a review.

### Order Endpoints
*   `GET /api/orders/`: (Protected) List orders. Customers see their placed orders, manufacturers see their received orders. Admins see all.
*   `GET /api/orders/{order_id}/`: (Protected) Retrieve a specific order. Accessible by customer, manufacturer involved, or admin.
*   `PATCH /api/orders/{order_id}/`: (Protected: Role-dependent) Update an order.
    *   Manufacturers can update `status` (e.g., to 'in_production', 'shipped'), `tracking_number`, `shipping_carrier`, `actual_ship_date`.
    *   Customers can update `status` to `cancelled_by_customer` (if order state allows), `shipping_address` (if not too late in process).
    *   Payload example by manufacturer: `{ "status": "shipped", "tracking_number": "123XYZ", "shipping_carrier": "UPS" }`
    *   Payload example by customer: `{ "status": "cancelled_by_customer", "cancellation_reason": "No longer needed." }`
*   Note: Orders are created automatically when a customer accepts a quote. There is no direct API endpoint for creating orders.


## Next Steps

*   Integrate a more comprehensive CAD library (e.g., `python-occ-core`, if environment permits) to support STEP/IGES files in the `analyze_cad_file` Celery task and potentially extract more detailed geometric insights.
*   Build out the quotation engine.
*   Flesh out Manufacturer profile management.
*   Add more comprehensive tests.
*   Containerize with Docker.
*   Set up CI/CD pipeline.
*   Develop the React frontend.

---

*This README is a work in progress and will be updated as development continues.*
