import { NextResponse } from "next/server";

import { runCaseAiSummaryAgainstBackend } from "@/lib/auth";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const data = await runCaseAiSummaryAgainstBackend(Number(id));
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to run AI summary";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
