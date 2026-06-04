import Link from "next/link";

export function ErrorState({
  title,
  description,
  actionHref,
  actionLabel
}: {
  title: string;
  description: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="error-state">
      <p className="state-kicker">Action needed</p>
      <h3>{title}</h3>
      <p>{description}</p>
      {actionHref && actionLabel ? (
        <Link href={actionHref} className="state-action">
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
