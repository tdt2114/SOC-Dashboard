import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, logoutAgainstBackend } from "@/lib/auth";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_COOKIE_NAME)?.value;

  if (refreshToken) {
    await logoutAgainstBackend(refreshToken);
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(ACCESS_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: 0
  });
  response.cookies.set(REFRESH_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: 0
  });
  return response;
}
