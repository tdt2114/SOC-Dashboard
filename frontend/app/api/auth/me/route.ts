import { NextRequest, NextResponse } from "next/server";

import { updateProfileAgainstBackend } from "@/lib/auth";

export async function PATCH(request: NextRequest) {
  try {
    const payload = (await request.json()) as {
      email: string;
      full_name: string | null;
    };
    const user = await updateProfileAgainstBackend(payload);
    return NextResponse.json({ user });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Profile update failed";
    return NextResponse.json({ detail }, { status: 400 });
  }
}
