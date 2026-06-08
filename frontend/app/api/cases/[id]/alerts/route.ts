import { NextRequest, NextResponse } from "next/server";

import { addAlertToCaseAgainstBackend } from "@/lib/auth";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const payload = (await request.json()) as { alert_id: string };
    const data = await addAlertToCaseAgainstBackend(Number(id), payload.alert_id);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to add alert to case";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
