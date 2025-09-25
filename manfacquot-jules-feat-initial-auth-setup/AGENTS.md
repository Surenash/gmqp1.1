# Agent Instructions for GMQP Project

## General Guidelines

1.  **Follow the Technical Specification:** The primary source of truth for requirements, architecture, and technology choices is the `Technical Specification: Global Manufacturing Quotation Platform (GMQP)` document.
2.  **Adhere to Django Best Practices:** Use Django conventions for project structure, model design, views, and forms/serializers.
3.  **Write Clear and Maintainable Code:** Comment complex logic. Write code that is easy for other developers (and agents) to understand.
4.  **Test-Driven Development (TDD):** Where practical, write tests before or alongside new features. Aim for good test coverage. All new backend features should be accompanied by relevant tests.
5.  **Security First:** Be mindful of security implications in all code you write, especially for authentication, authorization, and file handling, as outlined in the spec.
6.  **Incremental Commits:** Make small, logical commits. Write clear commit messages.
7.  **Update Documentation:** If you add or change features, ensure any relevant documentation (like `README.md` or API specs) is updated.

## Current Focus: Backend (Django)

*   The current phase of development is focused on the Django backend.
*   Refer to `gmqp_project/settings.py` for installed apps and configurations.
*   The custom user model is `accounts.User`.
*   The `Manufacturer` model and associated profile management APIs (`/api/manufacturers/` and `/api/manufacturers/profile/`) are implemented in the `accounts` app.
*   The `Design` model and APIs for managing designs (including S3 pre-signed URL generation for uploads) are implemented in the `designs` app.
    *   `POST /api/designs/upload-url`
    *   `POST /api/designs/` (to create DB record after S3 upload, which triggers async CAD analysis via Celery)
    *   `GET /api/designs/` (list user's designs)
    *   `GET/PATCH/DELETE /api/designs/{id}/`
    *   `POST /api/designs/{id}/generate-quotes/` (triggers automated quote generation, filtering manufacturers by material, advanced size check [permutations], and CNC capability).
*   Celery is configured with Redis as the broker for background tasks. The `analyze_cad_file` task now:
    *   Uses `numpy-stl` to process `.stl` files and extract volume, bbox, surface area, and triangle count (for complexity).
    *   Uses `steputils` for basic validation of `.step`/`.stp` files (detailed metrics not extracted).
    *   Marks `.iges`/`.igs` and other formats as `ANALYSIS_FAILED` due to lack of suitable libraries.
*   Manufacturer model now includes `markup_factor`. Its `capabilities` JSON field is expected to store:
    *   `materials_supported`: list of strings (e.g., `["ABS", "PLA"]`)
    *   `max_size_mm`: list of 3 numbers (e.g., `[X, Y, Z]`)
    *   `pricing_factors`: object containing material-specific costs/densities and machining parameters.
*   The `Quote` model and basic APIs are implemented in the `quotes` app:
    *   `POST /api/designs/{design_id}/quotes/`
    *   `GET /api/designs/{design_id}/quotes/`
    *   `GET/PATCH/DELETE /api/quotes/{quote_id}/`
*   The `Review` model and basic APIs are implemented in the `reviews` app:
    *   `POST /api/manufacturers/{manufacturer_id}/reviews/`
    *   `GET /api/manufacturers/{manufacturer_id}/reviews/`
    *   `GET/PATCH/DELETE /api/reviews/{review_id}/`
*   The `Order` model has been refined (new statuses, `actual_ship_date`, `cancellation_reason`). APIs in `orders` app now support updates by manufacturers (status, tracking) and customers (cancellation, shipping address) with permissions.
    *   `GET /api/orders/`
    *   `GET/PATCH /api/orders/{id}/` (PATCH for updates)

## Running Tests

Ensure all tests pass before submitting changes:

```bash
python manage.py test
```

Or for a specific app:

```bash
python manage.py test accounts
```

## Future Considerations (Agent Reminders)

*   **S3 Integration:** When implementing file uploads, ensure secure handling of credentials and pre-signed URLs as per the spec.
*   **Celery Tasks:** For CAD analysis, ensure tasks are idempotent if possible and handle potential failures gracefully.
*   **Database Schema:** Stick to the schema defined in the technical specification. If changes are needed, they should be justified and planned.
*   **API Endpoint Consistency:** Follow the API endpoint structure outlined in Section 6 of the technical specification.

---

*This AGENTS.md is a living document and may be updated.*
