'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

export default function PriceChart({ data }: { data: any[] }) {
  return (
    <LineChart width={500} height={300} data={data}>
      <Line type="monotone" dataKey="price" stroke="#8884d8" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
    </LineChart>
  );
}
