import { NextRequest, NextResponse } from "next/server";

import { resetUserPasswordAgainstBackend } from "@/lib/auth";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const payload = (await request.json()) as { new_password: string };
    await resetUserPasswordAgainstBackend(Number(id), payload.new_password);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to reset password";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
