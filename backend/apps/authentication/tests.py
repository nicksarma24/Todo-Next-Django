"""
Unit tests for Auth0JWTAuthentication. We simulate Auth0 by generating
our own RSA keypair, signing tokens with the private key exactly like
Auth0 would, and monkeypatching the JWKS cache to serve our public key
instead of calling out to a real Auth0 tenant.
"""
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import Account
from apps.authentication.auth0 import Auth0JWTAuthentication, _JWKSCache

TEST_DOMAIN = "test-tenant.us.auth0.com"
TEST_AUDIENCE = "https://api.example.com"


def _generate_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _make_token(private_key, kid="test-key", sub="auth0|abc123", audience=TEST_AUDIENCE,
                 issuer=f"https://{TEST_DOMAIN}/", email="user@example.com", expired=False):
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": audience,
        "iss": issuer,
        "iat": now - 10,
        "exp": now - 1 if expired else now + 3600,
        "email": email,
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})


@override_settings(AUTH0_DOMAIN=TEST_DOMAIN, AUTH0_AUDIENCE=TEST_AUDIENCE, AUTH0_ALGORITHMS=["RS256"])
class Auth0JWTAuthenticationTests(TestCase):
    def setUp(self):
        self.private_key, self.public_key = _generate_keypair()
        # Patch the JWKS cache to serve our test public key without a network call.
        _JWKSCache._keys = {"test-key": self.public_key}
        _JWKSCache._fetched_at = time.time()
        self.factory = APIRequestFactory()
        self.auth = Auth0JWTAuthentication()

    def _request_with_token(self, token):
        return self.factory.get("/api/todos/", HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_valid_token_creates_account_on_first_sight(self):
        token = _make_token(self.private_key)
        self.assertEqual(Account.objects.count(), 0)

        account, returned_token = self.auth.authenticate(self._request_with_token(token))

        self.assertEqual(returned_token, token)
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(account.auth0_user_id, "auth0|abc123")
        self.assertEqual(account.email, "user@example.com")

    def test_valid_token_reuses_existing_account(self):
        existing = Account.objects.create(auth0_user_id="auth0|abc123", email="old@example.com")
        token = _make_token(self.private_key, email="new@example.com")

        account, _ = self.auth.authenticate(self._request_with_token(token))

        self.assertEqual(account.id, existing.id)
        self.assertEqual(Account.objects.count(), 1)
        account.refresh_from_db()
        self.assertEqual(account.email, "new@example.com")

    def test_expired_token_is_rejected(self):
        token = _make_token(self.private_key, expired=True)
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._request_with_token(token))

    def test_wrong_audience_is_rejected(self):
        token = _make_token(self.private_key, audience="https://someone-else.example.com")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._request_with_token(token))

    def test_wrong_issuer_is_rejected(self):
        token = _make_token(self.private_key, issuer="https://not-my-tenant.auth0.com/")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(self._request_with_token(token))

    def test_token_signed_by_untrusted_key_is_rejected(self):
        other_private_key, _ = _generate_keypair()
        token = _make_token(other_private_key, kid="test-key")  # same kid, different key
        with self.assertRaises(Exception):
            # Signature won't match the cached public key for "test-key".
            self.auth.authenticate(self._request_with_token(token))

    def test_missing_authorization_header_returns_none(self):
        request = self.factory.get("/api/todos/")
        self.assertIsNone(self.auth.authenticate(request))

    def test_malformed_authorization_header_is_rejected(self):
        request = self.factory.get("/api/todos/", HTTP_AUTHORIZATION="Bearer")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)
