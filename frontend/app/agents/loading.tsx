import { PageLoadingState } from "@/components/PageLoadingState";

export default function AgentsLoading() {
  return <PageLoadingState title="Loading agents" rows={5} />;
}
