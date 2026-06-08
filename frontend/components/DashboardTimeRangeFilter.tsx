"use client";

import { FormEvent, useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { TIME_RANGE_OPTIONS, normalizeTimeRange } from "@/lib/timeRanges";

export function DashboardTimeRangeFilter({ value }: { value: string }) {
  const router = useRouter();
  const [selectedRange, setSelectedRange] = useState(normalizeTimeRange(value));
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setSelectedRange(normalizeTimeRange(value));
  }, [value]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextRange = normalizeTimeRange(selectedRange);

    startTransition(() => {
      router.push(`/dashboard?time_range=${encodeURIComponent(nextRange)}`);
    });
  }

  return (
    <form className="inline-filter-form" method="get" action="/dashboard" onSubmit={handleSubmit}>
      <label>
        <span>Time Range</span>
        <select
          name="time_range"
          value={selectedRange}
          onChange={(event) => setSelectedRange(normalizeTimeRange(event.target.value))}
        >
          {TIME_RANGE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={isPending}>
        {isPending ? "Applying" : "Apply"}
      </button>
    </form>
  );
}
