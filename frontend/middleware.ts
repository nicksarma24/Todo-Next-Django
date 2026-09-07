import type { NextRequest } from "next/server";

import { auth0 } from "./lib/auth0";

/**
 * Mounts Auth0's built-in routes (/auth/login, /auth/logout,
 * /auth/callback, /auth/profile, /auth/access-token) and keeps the
 * session cookie fresh on every request.
 */
export async function middleware(request: NextRequest) {
  return await auth0.middleware(request);
}

export const config = {
  matcher: [
    /*
     * Run on everything except static assets and image optimization
     * files, so auth routes and page navigations are always covered.
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
