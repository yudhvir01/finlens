import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatCurrency, formatDate } from "../lib/format";
import type { Account, Category, Transaction } from "../lib/types";

function useDebounced<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export function Transactions() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [accountId, setAccountId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const debouncedSearch = useDebounced(search);

  const accounts = useQuery({ queryKey: ["accounts"], queryFn: () => api.get<Account[]>("/accounts") });
  const categories = useQuery({ queryKey: ["categories"], queryFn: () => api.get<Category[]>("/categories") });

  const params = new URLSearchParams();
  if (debouncedSearch) params.set("search", debouncedSearch);
  if (accountId) params.set("account_id", accountId);
  if (categoryId) params.set("category_id", categoryId);
  params.set("limit", "100");

  const transactions = useQuery({
    queryKey: ["transactions", debouncedSearch, accountId, categoryId],
    queryFn: () => api.get<Transaction[]>(`/transactions?${params.toString()}`),
  });

  async function updateCategory(transactionId: string, newCategoryId: string) {
    await api.patch(`/transactions/${transactionId}`, { category_id: newCategoryId || null });
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["analytics"] });
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Transactions</h1>
      </header>

      <div className="flex flex-wrap gap-3">
        <input
          type="search"
          placeholder="Search merchant or description…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="min-w-[220px] flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
        />
        <select
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
        >
          <option value="">All accounts</option>
          {accounts.data?.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
        <select
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-1 focus:ring-ring"
        >
          <option value="">All categories</option>
          {categories.data?.filter((c) => c.parent_id !== null).map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border bg-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Merchant</th>
              <th className="px-4 py-3 font-medium">Category</th>
              <th className="px-4 py-3 text-right font-medium">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {transactions.data?.map((t) => (
              <tr key={t.id}>
                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">{formatDate(t.date)}</td>
                <td className="px-4 py-3">
                  <p className="font-medium text-foreground">{t.merchant ?? t.raw_description}</p>
                  <p className="truncate text-xs text-muted-foreground">{t.raw_description}</p>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={t.category?.id ?? ""}
                    onChange={(e) => updateCategory(t.id, e.target.value)}
                    className="rounded-md border border-input bg-background px-2 py-1 text-xs outline-none focus:border-ring focus:ring-1 focus:ring-ring"
                  >
                    <option value="">Uncategorized</option>
                    {categories.data?.filter((c) => c.parent_id !== null).map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </td>
                <td className={`whitespace-nowrap px-4 py-3 text-right font-mono-figures font-medium ${Number(t.amount) >= 0 ? "text-income" : "text-foreground"}`}>
                  {formatCurrency(t.amount)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {transactions.data && transactions.data.length === 0 && (
          <p className="p-8 text-center text-sm text-muted-foreground">No transactions match these filters.</p>
        )}
      </div>
    </div>
  );
}
