import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Account } from "../lib/types";

const ACCOUNT_TYPES = [
  { value: "bank", label: "Bank account" },
  { value: "credit_card", label: "Credit card" },
  { value: "wallet", label: "Wallet" },
];

export function Accounts() {
  const queryClient = useQueryClient();
  const accounts = useQuery({ queryKey: ["accounts"], queryFn: () => api.get<Account[]>("/accounts") });

  const [name, setName] = useState("");
  const [institution, setInstitution] = useState("");
  const [accountType, setAccountType] = useState("bank");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [editingId, setEditingId] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/accounts", { name, institution: institution || undefined, account_type: accountType });
      setName("");
      setInstitution("");
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create this account");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    await api.del(`/accounts/${id}`);
    queryClient.invalidateQueries({ queryKey: ["accounts"] });
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["analytics"] });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Accounts</h1>
        <p className="mt-1 text-sm text-muted-foreground">Add an account for each bank or card whose statements you want to track.</p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-5">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="name" className="text-xs text-muted-foreground">Name</label>
          <input
            id="name"
            required
            placeholder="HDFC Savings"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-44 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="institution" className="text-xs text-muted-foreground">Institution</label>
          <input
            id="institution"
            placeholder="HDFC Bank"
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            className="w-44 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="type" className="text-xs text-muted-foreground">Type</label>
          <select
            id="type"
            value={accountType}
            onChange={(e) => setAccountType(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
          >
            {ACCOUNT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
        >
          Add account
        </button>
        {error && <p className="w-full text-sm text-destructive">{error}</p>}
      </form>

      <div className="rounded-xl border border-border bg-card">
        <ul className="divide-y divide-border">
          {accounts.data?.map((a) =>
            editingId === a.id ? (
              <AccountEditRow key={a.id} account={a} onClose={() => setEditingId(null)} />
            ) : (
              <li key={a.id} className="flex items-center justify-between px-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-foreground">{a.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {a.institution ?? "—"} · {ACCOUNT_TYPES.find((t) => t.value === a.account_type)?.label}
                    {a.has_saved_password && " · PDF password saved"}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <button
                    type="button"
                    onClick={() => setEditingId(a.id)}
                    className="text-xs font-medium text-primary hover:underline"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(a.id)}
                    className="text-xs text-muted-foreground transition-colors hover:text-destructive"
                  >
                    Remove
                  </button>
                </div>
              </li>
            ),
          )}
          {accounts.data && accounts.data.length === 0 && (
            <li className="px-4 py-8 text-center text-sm text-muted-foreground">No accounts yet.</li>
          )}
        </ul>
      </div>
    </div>
  );
}

function AccountEditRow({ account, onClose }: { account: Account; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(account.name);
  const [institution, setInstitution] = useState(account.institution ?? "");
  const [accountType, setAccountType] = useState(account.account_type);

  const [password, setPassword] = useState("");
  const [passwordRevealed, setPasswordRevealed] = useState(false);
  const [passwordTouched, setPasswordTouched] = useState(false);
  const [revealing, setRevealing] = useState(false);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function revealPassword() {
    setRevealing(true);
    setError(null);
    try {
      const res = await api.get<{ password: string | null }>(`/accounts/${account.id}/statement-password`);
      setPassword(res.password ?? "");
      setPasswordRevealed(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the saved password");
    } finally {
      setRevealing(false);
    }
  }

  function clearPassword() {
    setPassword("");
    setPasswordRevealed(true);
    setPasswordTouched(true);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        name,
        institution: institution || null,
        account_type: accountType,
      };
      if (passwordTouched) payload.statement_password = password;

      await api.patch(`/accounts/${account.id}`, payload);
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save these changes");
    } finally {
      setSaving(false);
    }
  }

  return (
    <li className="px-4 py-4">
      <form onSubmit={handleSave} className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-muted-foreground">Name</label>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-44 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-muted-foreground">Institution</label>
            <input
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              className="w-44 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs text-muted-foreground">Type</label>
            <select
              value={accountType}
              onChange={(e) => setAccountType(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
            >
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-muted-foreground">Saved PDF statement password</label>
          {passwordRevealed ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="No password saved"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setPasswordTouched(true); }}
                className="w-56 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
              />
              {password && (
                <button type="button" onClick={clearPassword} className="text-xs text-muted-foreground hover:text-destructive">
                  Clear
                </button>
              )}
            </div>
          ) : account.has_saved_password ? (
            <div className="flex items-center gap-2">
              <span className="font-mono-figures text-sm text-muted-foreground">••••••••</span>
              <button
                type="button"
                onClick={revealPassword}
                disabled={revealing}
                className="text-xs font-medium text-primary hover:underline disabled:opacity-60"
              >
                {revealing ? "Loading…" : "Reveal / edit"}
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Not saved</span>
              <button
                type="button"
                onClick={() => setPasswordRevealed(true)}
                className="text-xs font-medium text-primary hover:underline"
              >
                Set one
              </button>
            </div>
          )}
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
          >
            Cancel
          </button>
        </div>
      </form>
    </li>
  );
}
