"""
Normalizes DRF error responses into a consistent shape:
    { "detail": "...", "code": "..." }
so the frontend can handle 400/401/403/404 uniformly.
"""
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    response.data = {
        "detail": str(detail) if detail is not None else "An error occurred.",
        "status_code": response.status_code,
    }
    return response
