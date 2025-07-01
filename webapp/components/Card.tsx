export function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md border bg-card text-card-foreground shadow-sm p-4">
      {children}
    </div>
  );
}
