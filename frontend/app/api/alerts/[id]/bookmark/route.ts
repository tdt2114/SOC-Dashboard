import { NextResponse } from "next/server";

import {
  bookmarkAlertAgainstBackend,
  getAlertBookmarkFromCookies,
  unbookmarkAlertAgainstBackend
} from "@/lib/auth";

export async function GET(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const data = await getAlertBookmarkFromCookies(params.id);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load alert bookmark";
    return NextResponse.json({ detail }, { status: 500 });
  }
}

export async function POST(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const data = await bookmarkAlertAgainstBackend(params.id);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to bookmark alert";
    return NextResponse.json({ detail }, { status: 500 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const data = await unbookmarkAlertAgainstBackend(params.id);
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to remove alert bookmark";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
