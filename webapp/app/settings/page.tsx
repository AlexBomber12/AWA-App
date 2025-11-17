import { NotificationPreferencesForm } from "@/components/features/settings/NotificationPreferencesForm";
import { PageBody, PageHeader } from "@/components/layout";

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Environment, notification, and RBAC controls will be wired here in PR-UI-1B and beyond."
      />
      <PageBody>
        <NotificationPreferencesForm />
      </PageBody>
    </>
  );
}
