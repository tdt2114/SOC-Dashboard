import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, loginAgainstBackend } from "@/lib/auth";

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as { username: string; password: string };
    const result = await loginAgainstBackend(payload);
    const response = NextResponse.json({ user: result.user });
    response.cookies.set(ACCESS_COOKIE_NAME, result.access_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: false,
      path: "/"
    });
    response.cookies.set(REFRESH_COOKIE_NAME, result.refresh_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: false,
      path: "/"
    });
    return response;
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Login failed";
    return NextResponse.json({ detail }, { status: 401 });
  }
}
