import { redirect } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { ProfileForms } from "@/components/ProfileForms";
import { getCurrentUserFromCookies } from "@/lib/auth";

export default async function ProfilePage() {
  const currentUser = await getCurrentUserFromCookies();

  if (!currentUser) {
    redirect("/login");
  }

  return (
    <AppShell title="Profile" eyebrow="Account" currentUser={currentUser}>
      <ProfileForms currentUser={currentUser} />
    </AppShell>
  );
}
