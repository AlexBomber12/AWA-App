import { Card } from "../../../components/Card";
import PriceChart from "../../../components/PriceChart";
import ApproveButton from "./approve-button";

interface SkuData {
  title: string;
  roi: number;
  fees: number;
  chartData: any[];
}

export default async function Page({ params }: { params: { asin: string } }) {
  const res = await fetch(`/sku/${params.asin}`);
  const data: SkuData = await res.json();

  return (
    <div className="grid gap-4">
      <Card>
        <h1 className="text-xl font-semibold">{data.title}</h1>
        <p>ROI: {data.roi}</p>
        <p>Fees: {data.fees}</p>
        <ApproveButton asin={params.asin} />
      </Card>
      <Card>
        <PriceChart data={data.chartData} />
      </Card>
    </div>
  );
}
