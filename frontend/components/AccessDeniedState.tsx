import { ErrorState } from "@/components/ErrorState";

export function AccessDeniedState({
  requiredRole,
  description
}: {
  requiredRole: string;
  description?: string;
}) {
  return (
    <ErrorState
      title={`${requiredRole} access required`}
      description={
        description ||
        "Your account is signed in, but this workspace is not available for your current role."
      }
      actionHref="/dashboard"
      actionLabel="Back to dashboard"
    />
  );
}
