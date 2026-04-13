import { NextRequest, NextResponse } from "next/server";

import { getAuditLogsFromCookies } from "@/lib/auth";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const data = await getAuditLogsFromCookies({
      action: searchParams.get("action") || undefined,
      q: searchParams.get("q") || undefined,
      page: searchParams.get("page") ? Number(searchParams.get("page")) : undefined,
      page_size: searchParams.get("page_size") ? Number(searchParams.get("page_size")) : undefined
    });
    return NextResponse.json(data);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to load audit logs";
    return NextResponse.json({ detail }, { status: 403 });
  }
}
