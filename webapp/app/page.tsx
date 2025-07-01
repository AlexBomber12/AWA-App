import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";

export default async function Dashboard() {
  const res = await fetch("/score", {
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
