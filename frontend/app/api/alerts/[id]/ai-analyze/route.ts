import { NextResponse } from "next/server";

import { runAlertAiAnalysisAgainstBackend } from "@/lib/auth";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const data = await runAlertAiAnalysisAgainstBackend(id);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to run AI analysis";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
