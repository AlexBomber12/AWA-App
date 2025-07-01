import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";

export const dynamic = 'force-dynamic';

export default async function Dashboard() {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const res = await fetch(`${base}/score`, {
    method: "POST",
    body: JSON.stringify(["ALL"]),
  });
  const data = await res.json();
  return (
    <Card>
      <DataTable data={data} />
    </Card>
  );
}
