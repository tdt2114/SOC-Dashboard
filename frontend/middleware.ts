import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE_NAME = "soc_access_token";
const REFRESH_COOKIE_NAME = "soc_refresh_token";
const API_BASE_URL =
  process.env.API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

function isProtectedPath(pathname: string) {
  return (
    pathname === "/dashboard" ||
    pathname === "/alerts" ||
    pathname.startsWith("/alerts/") ||
    pathname === "/agents" ||
    pathname === "/cases" ||
    pathname.startsWith("/cases/") ||
    pathname === "/profile" ||
    pathname === "/users" ||
    pathname === "/audit-logs" ||
    pathname === "/settings"
  );
}

function redirectToLogin(request: NextRequest, pathname: string) {
  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", pathname);
  const response = NextResponse.redirect(loginUrl);
  response.cookies.delete(ACCESS_COOKIE_NAME);
  response.cookies.delete(REFRESH_COOKIE_NAME);
  return response;
}

async function isAccessTokenValid(accessToken: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`
      },
      cache: "no-store"
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get(ACCESS_COOKIE_NAME)?.value;

  if (!isProtectedPath(pathname)) {
    return NextResponse.next();
  }

  if (!accessToken) {
    return redirectToLogin(request, pathname);
  }

  const isValid = await isAccessTokenValid(accessToken);
  if (!isValid) {
    return redirectToLogin(request, pathname);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/dashboard",
    "/alerts/:path*",
    "/agents",
    "/cases",
    "/cases/:path*",
    "/profile",
    "/users",
    "/audit-logs",
    "/settings"
  ]
};
