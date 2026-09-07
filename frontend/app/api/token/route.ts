import { NextResponse } from "next/server";

import { auth0 } from "@/lib/auth0";

/**
 * The browser calls this route (same-origin, so the Auth0 session
 * cookie is sent automatically) to obtain a short-lived access token
 * for calling the Django API directly from client components.
 *
 * Token refresh (via the rotating refresh token) is handled internally
 * by the SDK — the route always returns a currently-valid token, or
 * a 401 if there is no session.
 */
export async function GET() {
  const session = await auth0.getSession();
  if (!session) {
    return NextResponse.json({ detail: "Not authenticated." }, { status: 401 });
  }

  try {
    const result = await auth0.getAccessToken();
    // Different SDK versions have used slightly different shapes here;
    // support both defensively.
    const accessToken =
      (result as { token?: string; accessToken?: string }).token ??
      (result as { token?: string; accessToken?: string }).accessToken;

    if (!accessToken) {
      throw new Error("No access token returned by Auth0 SDK.");
    }

    return NextResponse.json({ accessToken });
  } catch (error) {
    console.error("Failed to get Auth0 access token:", error);
    return NextResponse.json(
      { detail: "Could not obtain an access token." },
      { status: 500 }
    );
  }
}
