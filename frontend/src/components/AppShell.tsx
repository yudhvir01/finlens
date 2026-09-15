import { useState, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthProvider";
import { LogoMark } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

function NavLink({ to, children }: { to: string; children: ReactNode }) {
  const { pathname } = useLocation();
  const active = pathname === to;
  return (
    <Link
      to={to}
      className={`rounded-md px-3 py-1.5 text-[15px] transition-colors ${
        active
          ? "bg-accent font-medium text-primary"
          : "text-muted-foreground hover:bg-accent hover:text-foreground"
      }`}
    >
      {children}
    </Link>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const [confirmSignOut, setConfirmSignOut] = useState(false);

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl">
      <aside className="flex w-60 shrink-0 flex-col border-r border-border px-5 py-7">
        <Link to="/" className="flex items-center gap-2.5 px-1">
          <LogoMark size={24} />
          <span className="text-[17px] font-semibold tracking-tight">Finlens</span>
        </Link>

        <nav className="mt-9 flex flex-col gap-0.5">
          <NavLink to="/">Dashboard</NavLink>
          <NavLink to="/transactions">Transactions</NavLink>
          <NavLink to="/upload">Upload</NavLink>
          <NavLink to="/accounts">Accounts</NavLink>
        </nav>

        <div className="mt-auto flex flex-col gap-2 pt-6">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setConfirmSignOut(true)}
            className="rounded-md px-3 py-1.5 text-left text-[15px] text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            Sign out
          </button>
          <p className="truncate px-3 text-xs text-muted-foreground">{user?.email}</p>
        </div>
      </aside>

      <div className="min-w-0 flex-1 px-8 py-10 sm:px-12">
        <div className="mx-auto max-w-5xl">{children}</div>
      </div>

      {confirmSignOut && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
          onClick={() => setConfirmSignOut(false)}
        >
          <div
            className="w-full max-w-sm rounded-lg border border-border bg-card p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-[15px] font-semibold">Sign out?</h2>
            <p className="mt-1.5 text-sm text-muted-foreground">
              You'll need to log back in with {user?.email} to see your data.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmSignOut(false)}
                className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={logout}
                className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition hover:opacity-90"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
