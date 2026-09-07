from rest_framework import viewsets

from .filters import TodoFilter
from .models import Todo
from .serializers import TodoSerializer


class TodoViewSet(viewsets.ModelViewSet):
    """
    CRUD for the authenticated account's own Todos.

    Security-critical detail: `get_queryset` scopes every query — list,
    retrieve, update, partial_update, and destroy — to
    `Todo.objects.filter(account=self.request.user)`.

    `self.request.user` here is the `Account` instance resolved by
    `Auth0JWTAuthentication` from the verified JWT (see
    apps/authentication/auth0.py). It is never taken from the URL, query
    string, or request body.

    Consequence: GET/PATCH/DELETE /api/todos/<id>/ for a Todo owned by a
    different account simply isn't in this queryset, so DRF's generic
    view logic raises Http404 — not 403. This deliberately avoids leaking
    "that id exists but isn't yours" (which itself is a minor information
    disclosure) while still fully preventing cross-account access
    (the IDOR case called out in the assignment).
    """

    serializer_class = TodoSerializer
    # DjangoFilterBackend + SearchFilter are wired globally in
    # settings.REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"].
    filterset_class = TodoFilter
    search_fields = ["title", "description"]

    def get_queryset(self):
        return Todo.objects.filter(account=self.request.user)

    def perform_create(self, serializer):
        # Ownership is set here, from the authenticated account — never
        # from any "account"/"user_id" field a client might send.
        serializer.save(account=self.request.user)
