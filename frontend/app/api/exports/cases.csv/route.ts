import { NextResponse } from "next/server";

import { exportCsvFromBackend } from "@/lib/auth";

export async function GET() {
  try {
    const csv = await exportCsvFromBackend("/api/exports/cases.csv");
    return new NextResponse(csv, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": 'attachment; filename="cases.csv"'
      }
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unable to export cases";
    return NextResponse.json({ detail }, { status: 500 });
  }
}
