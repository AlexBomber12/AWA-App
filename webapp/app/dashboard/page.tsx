import { DashboardPageClient } from "@/components/features/dashboard/DashboardPageClient";
import { PageBody, PageHeader } from "@/components/layout";
import { getServerAuthSession } from "@/lib/auth";

export default async function DashboardPage() {
  const session = await getServerAuthSession();
  const description = session?.user?.name
    ? `Operational pulse for ${session.user.name}.`
    : "Live KPIs and ROI trajectories for the ingestion pipeline.";

  return (
    <>
      <PageHeader title="Dashboard" description={description} />
      <PageBody>
        <DashboardPageClient />
      </PageBody>
    </>
  );
}
