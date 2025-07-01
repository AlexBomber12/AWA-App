import Link from 'next/link'

export default function Sidebar() {
  return (
    <aside className="w-48 border-r min-h-screen p-4">
      <nav className="space-y-2">
        <Link href="/" className="block rounded px-3 py-2 hover:bg-accent">
          Dashboard
        </Link>
        <Link href="/health" className="block rounded px-3 py-2 hover:bg-accent">
          Health
        </Link>
      </nav>
    </aside>
  )
}
