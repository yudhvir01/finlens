export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export interface Account {
  id: string;
  name: string;
  institution: string | null;
  account_type: string;
  last_four: string | null;
}

export interface Category {
  id: string;
  name: string;
  parent_id: string | null;
  icon: string | null;
  color: string | null;
}

export interface Transaction {
  id: string;
  account_id: string;
  date: string;
  amount: string;
  raw_description: string;
  merchant: string | null;
  category: Category | null;
  is_transfer: boolean;
  is_refund: boolean;
  is_recurring: boolean;
}

export interface Statement {
  id: string;
  account_id: string;
  filename: string;
  status: "processing" | "done" | "failed";
  error_message: string | null;
  transaction_count: number;
  period_start: string | null;
  period_end: string | null;
}

export interface Summary {
  income: string;
  expenses: string;
  net: string;
  savings_rate: number;
}

export interface MonthlyPoint {
  month: string;
  income: string;
  expenses: string;
  net: string;
}

export interface CategoryBreakdownItem {
  category_id: string | null;
  category_name: string;
  total: string;
  percentage: number;
  color: string | null;
}

export interface RecurringItem {
  merchant: string;
  average_amount: string;
  occurrences: number;
  category_name: string | null;
}
