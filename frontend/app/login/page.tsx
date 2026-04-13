import { redirect } from "next/navigation";

import { LoginForm } from "@/components/LoginForm";
import { getCurrentUserFromCookies } from "@/lib/auth";

export default async function LoginPage() {
  const currentUser = await getCurrentUserFromCookies();
  if (currentUser) {
    redirect("/alerts");
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <span className="auth-brand-mark">SOC</span>
          <div>
            <p className="eyebrow">SOC Dashboard</p>
            <h1>Sign In</h1>
          </div>
        </div>
        <p className="auth-caption">Access the internal security dashboard.</p>
        <LoginForm />
      </section>
    </main>
  );
}
