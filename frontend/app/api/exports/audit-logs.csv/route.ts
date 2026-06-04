import { NextRequest, NextResponse } from "next/server";

import { exportCsvFromBackend } from "@/lib/auth";

export async function GET(request: NextRequest) {
  try {
    const suffix = request.nextUrl.searchParams.toString();
    const csv = await exportCsvFromBackend(`/api/exports/audit-logs.csv${suffix ? `?${suffix}` : ""}`);
    return new NextResponse(csv, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": 'attachment; filename="audit-logs.csv"'
      }
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to export audit logs";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
