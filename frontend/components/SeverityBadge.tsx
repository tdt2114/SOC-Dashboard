import { SeverityLabel } from "@/lib/types";

export function SeverityBadge({ value }: { value: SeverityLabel }) {
  return <span className={`badge severity-${value}`}>{value}</span>;
}
