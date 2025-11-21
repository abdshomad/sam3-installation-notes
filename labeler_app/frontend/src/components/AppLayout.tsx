import { Link, NavLink, Outlet } from 'react-router-dom'

export const AppLayout = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/projects" className="text-lg font-semibold tracking-tight text-white">
            Labeler
          </Link>
          <nav className="space-x-6 text-sm text-slate-400">
            <NavLink to="/projects" className={({ isActive }) => (isActive ? 'text-white' : undefined)}>
              Projects
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}

