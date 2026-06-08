import { NextRequest, NextResponse } from "next/server";

import { getCaseFromCookies, updateCaseAgainstBackend } from "@/lib/auth";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const data = await getCaseFromCookies(Number(id));
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load case";
    return NextResponse.json({ detail }, { status: 500 });
  }
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const payload = (await request.json()) as {
      title?: string;
      description?: string | null;
      status?: string;
      severity?: string;
      owner_user_id?: number | null;
    };
    const data = await updateCaseAgainstBackend(Number(id), payload);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to update case";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
