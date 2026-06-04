import { redirect } from "next/navigation";

import { AccessDeniedState } from "@/components/AccessDeniedState";
import { AppShell } from "@/components/AppShell";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { UserManagement } from "@/components/UserManagement";
import { getCurrentUserFromCookies, getUsersAdminDataFromCookies } from "@/lib/auth";

export default async function UsersPage() {
  const currentUser = await getCurrentUserFromCookies();

  if (!currentUser) {
    redirect("/login");
  }

  if (!currentUser.is_superuser) {
    return (
      <AppShell title="Users" eyebrow="Administration" currentUser={currentUser}>
        <div className="panel">
          <AccessDeniedState
            requiredRole="Superadmin"
            description="User creation, role assignment, and account activation are restricted to superadmin users."
          />
        </div>
      </AppShell>
    );
  }

  try {
    const data = await getUsersAdminDataFromCookies();

    return (
      <AppShell title="Users" eyebrow="Administration" currentUser={currentUser}>
        {data.items.length === 0 ? (
          <div className="panel">
            <EmptyState
              title="No users found"
              description="Create the first analyst or admin account from this page."
              actionHref="/dashboard"
              actionLabel="Back to dashboard"
            />
          </div>
        ) : null}
        <UserManagement users={data.items} departments={data.departments} roles={data.roles} />
      </AppShell>
    );
  } catch (error) {
    return (
      <AppShell title="Users" eyebrow="Administration" currentUser={currentUser}>
        <div className="panel">
          <ErrorState
            title="Unable to load user management"
            description={error instanceof Error ? error.message : "Unknown admin error"}
            actionHref="/dashboard"
            actionLabel="Back to dashboard"
          />
        </div>
      </AppShell>
    );
  }
}
