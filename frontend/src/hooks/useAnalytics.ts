import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { CategoryBreakdownItem, MonthlyPoint, RecurringItem, Summary } from "../lib/types";

export function useSummary(month: string) {
  return useQuery({
    queryKey: ["analytics", "summary", month],
    queryFn: () => api.get<Summary>(`/analytics/summary?month=${month}`),
  });
}

export function useMonthly(months = 6) {
  return useQuery({
    queryKey: ["analytics", "monthly", months],
    queryFn: () => api.get<MonthlyPoint[]>(`/analytics/monthly?months=${months}`),
  });
}

export function useCategoryBreakdown(month: string) {
  return useQuery({
    queryKey: ["analytics", "categories", month],
    queryFn: () => api.get<CategoryBreakdownItem[]>(`/analytics/categories?month=${month}`),
  });
}

export function useRecurring() {
  return useQuery({
    queryKey: ["analytics", "recurring"],
    queryFn: () => api.get<RecurringItem[]>("/analytics/recurring"),
  });
}
