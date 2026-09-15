import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { api, ApiError } from "../lib/api";
import type { Account, Statement } from "../lib/types";

export function Upload() {
  const queryClient = useQueryClient();
  const accounts = useQuery({ queryKey: ["accounts"], queryFn: () => api.get<Account[]>("/accounts") });
  const statements = useQuery({ queryKey: ["statements"], queryFn: () => api.get<Statement[]>("/statements") });

  const [accountId, setAccountId] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const selectedAccountId = accountId || accounts.data?.[0]?.id || "";

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
      await api.upload(`/accounts/${selectedAccountId}/statements`, formData);
      queryClient.invalidateQueries({ queryKey: ["statements"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Upload a statement</h1>
        <p className="mt-1 text-sm text-muted-foreground">CSV works best. PDF support handles statements with a real tabular layout.</p>
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

      {error && <p className="text-sm text-destructive">{error}</p>}

      {statements.data && statements.data.length > 0 && (
        <div className="rounded-xl border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="px-4 py-3 font-medium">File</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Transactions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {statements.data.map((s) => (
                <tr key={s.id}>
                  <td className="px-4 py-3 text-foreground">{s.filename}</td>
                  <td className="px-4 py-3">
                    {s.status === "done" && <span className="text-income">Parsed</span>}
                    {s.status === "processing" && <span className="text-muted-foreground">Processing…</span>}
                    {s.status === "failed" && <span title={s.error_message ?? ""} className="text-destructive">Failed</span>}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{s.status === "done" ? s.transaction_count : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
