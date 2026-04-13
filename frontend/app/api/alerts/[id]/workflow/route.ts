import { NextResponse } from "next/server";

import { getAlertWorkflowFromCookies } from "@/lib/auth";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const data = await getAlertWorkflowFromCookies(params.id);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load alert workflow";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
