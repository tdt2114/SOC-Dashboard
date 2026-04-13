import { ReactNode } from "react";

function formatValue(value: ReactNode) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  return value;
}

export function KeyValueGrid({
  items
}: {
  items: Array<{ label: string; value: ReactNode }>;
}) {
  return (
    <div className="key-value-grid">
      {items.map((item) => (
        <div key={item.label} className="key-value-item">
          <span className="key-label">{item.label}</span>
          <span className="key-value">{formatValue(item.value)}</span>
        </div>
      ))}
    </div>
  );
}
