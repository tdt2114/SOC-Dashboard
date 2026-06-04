import { redirect } from "next/navigation";

import { AccessDeniedState } from "@/components/AccessDeniedState";
import { AppShell } from "@/components/AppShell";
import { ErrorState } from "@/components/ErrorState";
import { KeyValueGrid } from "@/components/KeyValueGrid";
import { getCurrentUserFromCookies, getSystemSettingsFromCookies } from "@/lib/auth";

export default async function SettingsPage() {
  const currentUser = await getCurrentUserFromCookies();
  if (!currentUser) {
    redirect("/login");
  }
  if (!currentUser.is_superuser) {
    return (
      <AppShell title="Settings" eyebrow="Superadmin" currentUser={currentUser}>
        <section className="panel">
          <AccessDeniedState
            requiredRole="Superadmin"
            description="Runtime configuration includes deployment and integration details, so it is visible only to superadmin users."
          />
        </section>
      </AppShell>
    );
  }

  try {
    const settings = await getSystemSettingsFromCookies();
    return (
      <AppShell title="Settings" eyebrow="Superadmin" currentUser={currentUser}>
        <section className="panel stack">
          <div className="panel-header">
            <div>
              <h3>System Settings</h3>
              <p>Read-only operational configuration for Repo B. Secrets are intentionally hidden.</p>
            </div>
            <span className={`status-pill status-${settings.database === "ok" ? "active" : "disconnected"}`}>
              DB {settings.database}
            </span>
          </div>

          <KeyValueGrid
            items={[
              { label: "App Environment", value: settings.app_env },
              { label: "Data Mode", value: settings.mode },
              { label: "Database", value: settings.database },
              { label: "Default Time Range", value: settings.default_time_range },
              { label: "Default Page Size", value: settings.default_page_size },
              { label: "Max Page Size", value: settings.max_page_size },
              { label: "Verify TLS", value: settings.verify_tls ? "true" : "false" },
              { label: "Wazuh API URL", value: settings.wazuh_api_base_url },
              { label: "Wazuh Indexer URL", value: settings.wazuh_indexer_url },
              { label: "Alert Index Pattern", value: settings.wazuh_alert_index_pattern }
            ]}
          />
        </section>
      </AppShell>
    );
  } catch (error) {
    return (
      <AppShell title="Settings" eyebrow="Superadmin" currentUser={currentUser}>
        <section className="panel">
          <ErrorState
            title="System settings are unavailable"
            description={error instanceof Error ? error.message : "Unknown settings error"}
            actionHref="/dashboard"
            actionLabel="Back to dashboard"
          />
        </section>
      </AppShell>
    );
  }
}
