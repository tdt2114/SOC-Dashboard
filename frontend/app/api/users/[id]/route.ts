import { NextRequest, NextResponse } from "next/server";

import { updateUserAgainstBackend } from "@/lib/auth";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const payload = (await request.json()) as {
      email?: string;
      full_name?: string | null;
      department_id?: number | null;
      is_active?: boolean;
      is_superuser?: boolean;
      roles?: string[];
    };
    await updateUserAgainstBackend(Number(id), payload);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to update user";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
