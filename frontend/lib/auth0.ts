import { Auth0Client } from "@auth0/nextjs-auth0/server";

/**
 * Single shared Auth0 client for the app.
 *
 * `authorizationParameters.audience` is what makes Auth0 issue a JWT
 * *access token* scoped to our Django API (rather than an opaque/JWE
 * token meant only for the /userinfo endpoint). This must match
 * AUTH0_AUDIENCE on the Django backend exactly.
 */
export const auth0 = new Auth0Client({
  authorizationParameters: {
    audience: process.env.AUTH0_AUDIENCE,
    scope: process.env.AUTH0_SCOPE || "openid profile email offline_access",
  },
});
