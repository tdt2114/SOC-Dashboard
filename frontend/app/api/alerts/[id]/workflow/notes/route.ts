import { NextRequest, NextResponse } from "next/server";

import { addAlertNoteAgainstBackend } from "@/lib/auth";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const payload = (await request.json()) as {
      body: string;
    };
    const data = await addAlertNoteAgainstBackend(params.id, payload);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to add alert note";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
