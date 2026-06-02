import { NextResponse } from "next/server";

import { deleteSavedSearchAgainstBackend } from "@/lib/auth";

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    await deleteSavedSearchAgainstBackend(Number(params.id));
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to delete saved search";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
