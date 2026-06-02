import { NextRequest, NextResponse } from "next/server";

import { createCaseAgainstBackend, getCasesFromCookies } from "@/lib/auth";

export async function GET() {
  try {
    const data = await getCasesFromCookies();
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load cases";
    return NextResponse.json({ detail }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      title: string;
      description?: string | null;
      status?: string;
      severity?: string;
      owner_user_id?: number | null;
      alert_id?: string | null;
    };
    const data = await createCaseAgainstBackend(payload);
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to create case";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
