import { NextResponse } from "next/server";

import { markNotificationReadAgainstBackend } from "@/lib/auth";

export async function POST(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    await markNotificationReadAgainstBackend(Number(params.id));
    return new Response(null, { status: 204 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to mark notification read";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
