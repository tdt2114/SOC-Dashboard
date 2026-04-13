import { NextRequest, NextResponse } from "next/server";

import { changePasswordAgainstBackend } from "@/lib/auth";

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      current_password: string;
      new_password: string;
    };
    await changePasswordAgainstBackend(payload);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Password change failed";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
