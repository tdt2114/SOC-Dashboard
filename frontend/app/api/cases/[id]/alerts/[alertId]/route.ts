import { NextResponse } from "next/server";

import { removeAlertFromCaseAgainstBackend } from "@/lib/auth";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string; alertId: string }> }
) {
  try {
    const { id, alertId } = await params;
    const data = await removeAlertFromCaseAgainstBackend(Number(id), alertId);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to remove alert from case";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
