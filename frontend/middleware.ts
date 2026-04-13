import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE_NAME = "soc_access_token";

function isProtectedPath(pathname: string) {
  return (
    pathname === "/alerts" ||
    pathname.startsWith("/alerts/") ||
    pathname === "/agents" ||
    pathname === "/profile" ||
    pathname === "/users" ||
    pathname === "/audit-logs"
  );
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasAccessToken = Boolean(request.cookies.get(ACCESS_COOKIE_NAME)?.value);

  if (isProtectedPath(pathname) && !hasAccessToken) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname === "/login" && hasAccessToken) {
    return NextResponse.redirect(new URL("/alerts", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/alerts/:path*", "/agents", "/profile", "/users", "/audit-logs"]
};
