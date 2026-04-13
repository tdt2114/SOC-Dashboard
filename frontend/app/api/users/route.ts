import { NextRequest, NextResponse } from "next/server";

import { createUserAgainstBackend, getUsersAdminDataFromCookies } from "@/lib/auth";

export async function GET() {
  try {
    const data = await getUsersAdminDataFromCookies();
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load users";
    return NextResponse.json({ detail }, { status: 403 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      username: string;
      email: string;
      password: string;
      full_name: string | null;
      department_id: number | null;
      is_active: boolean;
      is_superuser: boolean;
      roles: string[];
    };
    await createUserAgainstBackend(payload);
    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to create user";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
