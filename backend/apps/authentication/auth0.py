"""
Auth0 JWT authentication for Django REST Framework.

This is the single place where "who is making this request" is decided.
It validates the incoming Bearer token's signature and claims against
Auth0's public JWKS (fetched from the tenant's `/.well-known/jwks.json`
endpoint), then resolves the corresponding local `Account` from the
token's `sub` claim.

Crucially: the authenticated account is derived ONLY from the verified
token. Views must never accept a user/account id from the request body,
query params, or URL — see apps/todos/views.py for how this is enforced
at the query level.
"""
import time

import jwt
import requests
from django.conf import settings
from rest_framework import authentication, exceptions

from apps.accounts.models import Account


class _JWKSCache:
    """Tiny in-process cache for Auth0's JSON Web Key Set.

    Avoids hitting Auth0 on every single request while still refreshing
    periodically in case keys are rotated.
    """

    _keys = None
    _fetched_at = 0
    _TTL_SECONDS = 60 * 60  # 1 hour

    @classmethod
    def get_signing_key(cls, kid: str):
        if cls._keys is None or (time.time() - cls._fetched_at) > cls._TTL_SECONDS:
            cls._refresh()
        key = cls._keys.get(kid) if cls._keys else None
        if key is None:
            # Key not found; refresh once in case of recent rotation, then give up.
            cls._refresh()
            key = cls._keys.get(kid) if cls._keys else None
        return key

    @classmethod
    def _refresh(cls):
        if not settings.AUTH0_DOMAIN:
            cls._keys = {}
            return
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        jwks = response.json()
        cls._keys = {
            jwk["kid"]: jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
            for jwk in jwks.get("keys", [])
        }
        cls._fetched_at = time.time()


class Auth0JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header:
            return None  # No credentials supplied; let other checks (IsAuthenticated) reject.

        parts = auth_header.split()
        if parts[0].lower() != self.keyword.lower():
            return None
        if len(parts) == 1:
            raise exceptions.AuthenticationFailed("Malformed Authorization header: no token found.")
        if len(parts) > 2:
            raise exceptions.AuthenticationFailed("Malformed Authorization header: token contains spaces.")

        token = parts[1]
        payload = self._decode_token(token)
        account = self._resolve_account(payload)
        return (account, token)

    def _decode_token(self, token: str) -> dict:
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.DecodeError as exc:
            raise exceptions.AuthenticationFailed("Invalid token header.") from exc

        signing_key = _JWKSCache.get_signing_key(unverified_header.get("kid"))
        if signing_key is None:
            raise exceptions.AuthenticationFailed("Unable to find an appropriate signing key.")

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=settings.AUTH0_ALGORITHMS,
                audience=settings.AUTH0_AUDIENCE or None,
                issuer=f"https://{settings.AUTH0_DOMAIN}/",
            )
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.AuthenticationFailed("Token has expired.") from exc
        except jwt.InvalidAudienceError as exc:
            raise exceptions.AuthenticationFailed("Invalid token audience.") from exc
        except jwt.InvalidIssuerError as exc:
            raise exceptions.AuthenticationFailed("Invalid token issuer.") from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed("Invalid token.") from exc

        return payload

    def _resolve_account(self, payload: dict) -> Account:
        """
        Map the verified token's `sub` claim to a local Account,
        creating one on first sight. This is the ONLY place an Account
        is looked up for a request — the client never supplies this id.
        """
        sub = payload.get("sub")
        if not sub:
            raise exceptions.AuthenticationFailed("Token missing 'sub' claim.")

        email = (
            payload.get("email")
            or payload.get(f"{settings.AUTH0_AUDIENCE}/email", "")
            or ""
        )

        account, _created = Account.objects.get_or_create(
            auth0_user_id=sub,
            defaults={"email": email},
        )
        # Keep email reasonably fresh if Auth0 sends it in the token.
        if email and account.email != email:
            account.email = email
            account.save(update_fields=["email"])

        return account

    def authenticate_header(self, request):
        return self.keyword
