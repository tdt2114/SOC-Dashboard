import { NextResponse } from "next/server";

import { approvePendingActionAgainstBackend } from "@/lib/auth";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  try {
    const { token } = await params;
    const data = await approvePendingActionAgainstBackend(token);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to approve action";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
