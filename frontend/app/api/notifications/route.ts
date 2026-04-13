import { NextResponse } from "next/server";

import { getNotificationsFromCookies } from "@/lib/auth";

export async function GET() {
  try {
    const data = await getNotificationsFromCookies();
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load notifications";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
