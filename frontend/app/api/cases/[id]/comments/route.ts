import { NextRequest, NextResponse } from "next/server";

import { addCaseCommentAgainstBackend } from "@/lib/auth";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const payload = (await request.json()) as { body: string };
    const data = await addCaseCommentAgainstBackend(Number(params.id), payload.body);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to add case comment";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
