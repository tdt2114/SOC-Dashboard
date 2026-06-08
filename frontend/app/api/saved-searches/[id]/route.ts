import { NextResponse } from "next/server";

import { deleteSavedSearchAgainstBackend } from "@/lib/auth";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    await deleteSavedSearchAgainstBackend(Number(id));
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to delete saved search";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
