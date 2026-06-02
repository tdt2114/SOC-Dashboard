import { NextRequest, NextResponse } from "next/server";

import { createSavedSearchAgainstBackend, getSavedSearchesFromCookies } from "@/lib/auth";

export async function GET() {
  try {
    const data = await getSavedSearchesFromCookies();
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load saved searches";
    return NextResponse.json({ detail }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      name: string;
      filters: Record<string, string>;
    };
    await createSavedSearchAgainstBackend(payload);
    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to create saved search";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
