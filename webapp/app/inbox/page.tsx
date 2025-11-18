import { InboxPage } from "@/components/features/inbox/InboxPage";
import { PageBody, PageHeader } from "@/components/layout";
import { getServerAuthSession } from "@/lib/auth";
import { can, getUserRolesFromSession } from "@/lib/permissions/server";

export const metadata = {
  title: "Inbox | AWA",
};

export default async function InboxRoutePage() {
  const session = await getServerAuthSession();
  const roles = getUserRolesFromSession(session);
  const canViewInbox = can({ resource: "inbox", action: "view", roles });

  if (!canViewInbox) {
    return (
      <>
        <PageHeader
          title="Inbox"
          description="Operator triage workspace for Decision Engine and ROI tasks."
          breadcrumbs={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Inbox", active: true },
          ]}
        />
        <PageBody>
          <div className="rounded-2xl border border-border bg-muted/30 p-8 text-center">
            <p className="text-base font-semibold">Not allowed</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Ask an administrator to grant inbox access to view Decision Engine tasks.
            </p>
          </div>
        </PageBody>
      </>
    );
  }

  return <InboxPage />;
}
