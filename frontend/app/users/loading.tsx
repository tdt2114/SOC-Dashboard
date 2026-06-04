import { PageLoadingState } from "@/components/PageLoadingState";

export default function UsersLoading() {
  return <PageLoadingState title="Loading user management" rows={5} />;
}
