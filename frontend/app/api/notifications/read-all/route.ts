import { NextResponse } from "next/server";

import { markAllNotificationsReadAgainstBackend } from "@/lib/auth";

export async function POST() {
  try {
    await markAllNotificationsReadAgainstBackend();
    return new Response(null, { status: 204 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to mark notifications read";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
