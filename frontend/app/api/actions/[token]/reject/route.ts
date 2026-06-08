import { NextRequest, NextResponse } from "next/server";

import { rejectPendingActionAgainstBackend } from "@/lib/auth";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ token: string }> }
) {
  try {
    const { token } = await params;
    const payload = (await request.json().catch(() => ({}))) as { reason?: string | null };
    const data = await rejectPendingActionAgainstBackend(token, payload.reason ?? null);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to reject action";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
