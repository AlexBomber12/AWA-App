import { DecisionEnginePage } from "@/components/features/decision/DecisionEnginePage";
import { PageBody, PageHeader } from "@/components/layout";
import { getServerAuthSession } from "@/lib/auth";
import { can, getUserRolesFromSession } from "@/lib/permissions/server";

export const metadata = {
  title: "Decision Engine | AWA",
};

export default async function DecisionRoutePage() {
  const session = await getServerAuthSession();
  const roles = getUserRolesFromSession(session);
  const canViewDecision = can({ resource: "decision", action: "view", roles });

  if (!canViewDecision) {
    return (
      <>
        <PageHeader
          title="Decision Engine"
          description="Configure rules and run simulations."
          breadcrumbs={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Decision Engine", active: true },
          ]}
        />
        <PageBody>
          <div className="rounded-2xl border border-border bg-muted/30 p-8 text-center">
            <p className="text-base font-semibold">Not allowed</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Only administrators can access the Decision Engine workspace.
            </p>
          </div>
        </PageBody>
      </>
    );
  }

  return <DecisionEnginePage />;
}
