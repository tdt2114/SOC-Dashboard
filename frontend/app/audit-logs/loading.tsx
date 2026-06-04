import { PageLoadingState } from "@/components/PageLoadingState";

export default function AuditLogsLoading() {
  return <PageLoadingState title="Loading audit logs" rows={6} />;
}
