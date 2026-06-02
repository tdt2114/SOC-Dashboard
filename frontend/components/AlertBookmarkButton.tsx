"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AlertBookmarkResponse } from "@/lib/types";

export function AlertBookmarkButton({
  alertId,
  initialBookmark
}: {
  alertId: string;
  initialBookmark: AlertBookmarkResponse;
}) {
  const router = useRouter();
  const [bookmark, setBookmark] = useState(initialBookmark);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleToggle() {
    setError(null);
    setIsSaving(true);
    try {
      const response = await fetch(`/api/alerts/${encodeURIComponent(alertId)}/bookmark`, {
        method: bookmark.is_bookmarked ? "DELETE" : "POST"
      });
      const payload = (await response.json()) as AlertBookmarkResponse | { detail?: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail || "Unable to update bookmark" : "Unable to update bookmark");
      }
      setBookmark(payload as AlertBookmarkResponse);
      router.refresh();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Unable to update bookmark");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="bookmark-action">
      <button
        type="button"
        className={`secondary-button bookmark-button${bookmark.is_bookmarked ? " bookmark-button-active" : ""}`}
        onClick={handleToggle}
        disabled={isSaving}
      >
        {isSaving ? "Saving..." : bookmark.is_bookmarked ? "Bookmarked" : "Bookmark"}
      </button>
      {error ? <p className="form-error compact-error">{error}</p> : null}
    </div>
  );
}
