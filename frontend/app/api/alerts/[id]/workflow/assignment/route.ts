import { NextRequest, NextResponse } from "next/server";

import { assignAlertAgainstBackend } from "@/lib/auth";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const payload = (await request.json()) as {
      assigned_user_id: number | null;
    };
    const data = await assignAlertAgainstBackend(id, payload);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to assign alert";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
