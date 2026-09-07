from django.db import models


class Account(models.Model):
    """
    Local representation of an authenticated Auth0 user.

    We never let the frontend choose or supply this record directly.
    Instead, `Auth0JWTAuthentication` resolves (and lazily creates) the
    Account from the validated token's `sub` claim on every request, so
    the account a request acts as is always derived from the token, not
    from client-supplied data.
    """

    auth0_user_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="The Auth0 'sub' claim, e.g. 'auth0|abc123' or 'google-oauth2|123'.",
    )
    email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email or self.auth0_user_id

    # DRF's IsAuthenticated permission (and other Django auth machinery)
    # expects `request.user` to expose a user-like interface. Account is
    # deliberately NOT a Django User (there's no username/password —
    # identity comes entirely from Auth0), so we provide the minimal
    # surface needed here rather than pulling in the full auth system.
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False
