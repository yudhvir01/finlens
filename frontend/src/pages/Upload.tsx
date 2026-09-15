import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Account, Statement } from "../lib/types";

interface UnlockTarget {
  accountId: string;
  statementId: string | null; // null when triggered by a fresh upload rather than an existing row
  filename: string;
  file: File | null; // already in hand if this came straight from a drop/pick; otherwise the form asks for it
}

export function Upload() {
  const queryClient = useQueryClient();
  const accounts = useQuery({ queryKey: ["accounts"], queryFn: () => api.get<Account[]>("/accounts") });
  const statements = useQuery({ queryKey: ["statements"], queryFn: () => api.get<Statement[]>("/statements") });

  const [accountId, setAccountId] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [unlockTarget, setUnlockTarget] = useState<UnlockTarget | null>(null);
  const [unlockFile, setUnlockFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");
  const [rememberPassword, setRememberPassword] = useState(true);
  const fileInput = useRef<HTMLInputElement>(null);
  const unlockFileInput = useRef<HTMLInputElement>(null);

  const selectedAccountId = accountId || accounts.data?.[0]?.id || "";

  function invalidateAfterUpload() {
    queryClient.invalidateQueries({ queryKey: ["statements"] });
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["analytics"] });
  }

  async function handleFile(file: File) {
    if (!selectedAccountId) {
      setError("Add an account first — see the Accounts page.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const statement = await api.upload<Statement>(`/accounts/${selectedAccountId}/statements`, formData);

      if (statement.status === "password_required") {
        setUnlockTarget({ accountId: selectedAccountId, statementId: null, filename: file.name, file });
      } else if (statement.status === "failed") {
        setError(statement.error_message ?? "Couldn't parse this statement.");
      }
      invalidateAfterUpload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function handleUnlockSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!unlockTarget) return;
    const file = unlockTarget.file ?? unlockFile;
    if (!file) {
      setError("Choose the file again to unlock it.");
      return;
    }

    setError(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("password", password);
      formData.append("remember_password", String(rememberPassword));
      const statement = await api.upload<Statement>(`/accounts/${unlockTarget.accountId}/statements`, formData);

      if (statement.status === "password_required") {
        setError(statement.error_message ?? "That password didn't work.");
        return;
      }
      if (statement.status === "failed") {
        setError(statement.error_message ?? "Couldn't parse this statement.");
      }
      // Retiring an old stuck row once its retry lands somewhere definite.
      if (unlockTarget.statementId) {
        await api.del(`/statements/${unlockTarget.statementId}`);
      }
      setUnlockTarget(null);
      setUnlockFile(null);
      setPassword("");
      invalidateAfterUpload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function startUnlock(statement: Statement) {
    setError(null);
    setPassword("");
    setUnlockFile(null);
    setUnlockTarget({
      accountId: statement.account_id,
      statementId: statement.id,
      filename: statement.filename,
      file: null,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Upload a statement</h1>
        <p className="mt-1 text-sm text-muted-foreground">CSV works best. PDF support handles statements with a real tabular layout — password-protected PDFs are fine too.</p>
      </header>

      {accounts.data && accounts.data.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="account" className="text-sm text-muted-foreground">Account</label>
          <select
            id="account"
            value={selectedAccountId}
            onChange={(e) => setAccountId(e.target.value)}
            className="w-64 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
          >
            {accounts.data.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </div>
      )}

      {unlockTarget ? (
        <form
          onSubmit={handleUnlockSubmit}
          className="flex flex-col gap-4 rounded-xl border border-border bg-card p-6"
        >
          <p className="text-sm font-medium text-foreground">{unlockTarget.filename}</p>

          {!unlockTarget.file && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="unlock-file" className="text-sm text-muted-foreground">
                Re-select the file (it isn't kept on the server between attempts)
              </label>
              <input
                id="unlock-file"
                ref={unlockFileInput}
                type="file"
                accept=".csv,.pdf"
                required
                onChange={(e) => setUnlockFile(e.target.files?.[0] ?? null)}
                className="text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-secondary file:px-3 file:py-1.5 file:text-sm file:text-secondary-foreground"
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label htmlFor="pdf-password" className="text-sm text-muted-foreground">PDF password</label>
            <input
              id="pdf-password"
              type="password"
              autoFocus
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-64 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={rememberPassword}
              onChange={(e) => setRememberPassword(e.target.checked)}
              className="h-4 w-4 rounded border-input"
            />
            Remember this password for future statements on this account
          </label>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={uploading}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
            >
              {uploading ? "Unlocking…" : "Unlock and parse"}
            </button>
            <button
              type="button"
              onClick={() => { setUnlockTarget(null); setUnlockFile(null); setPassword(""); setError(null); }}
              className="rounded-md px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
          }}
          onClick={() => fileInput.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
            dragging ? "border-primary bg-accent" : "border-border hover:border-muted-foreground"
          }`}
        >
          <p className="text-sm font-medium text-foreground">
            {uploading ? "Parsing statement…" : "Drop a CSV or PDF here, or click to browse"}
          </p>
          <p className="text-xs text-muted-foreground">Up to 15MB</p>
          <input
            ref={fileInput}
            type="file"
            accept=".csv,.pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {statements.data && statements.data.length > 0 && (
        <div className="rounded-xl border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Transactions</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {statements.data.map((s) => (
                <tr key={s.id}>
                  <td className="px-4 py-3 text-foreground">{s.filename}</td>
                  <td className="px-4 py-3">
                    {s.status === "done" && <span className="text-income">Parsed</span>}
                    {s.status === "processing" && <span className="text-muted-foreground">Processing…</span>}
                    {s.status === "password_required" && <span className="text-expense">Needs password</span>}
                    {s.status === "failed" && <span title={s.error_message ?? ""} className="text-destructive">Failed</span>}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{s.status === "done" ? s.transaction_count : "—"}</td>
                  <td className="px-4 py-3 text-right">
                    {s.status === "password_required" && (
                      <button
                        type="button"
                        onClick={() => startUnlock(s)}
                        className="text-xs font-medium text-primary hover:underline"
                      >
                        Unlock
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
