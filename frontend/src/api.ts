const API_URL = 'http://127.0.0.1:8000'

export type TransactionType = 'income' | 'expense'

export interface Transaction {
  id: number
  date: string
  amount: number
  type: TransactionType
  category: string
  description: string
}

export interface CategoryExpense {
  category: string
  amount: number
}

export interface FinancialSummary {
  start_date: string
  end_date: string
  total_income: number
  total_expenses: number
  balance: number
  expenses_by_category: CategoryExpense[]
  transactions_count: number
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`)

  if (!response.ok) {
    throw new Error(`Ошибка API: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<T>
}

export function getTransactions(): Promise<Transaction[]> {
  return request<Transaction[]>('/transactions')
}

export function getFinancialSummary(
  startDate: string,
  endDate: string,
): Promise<FinancialSummary> {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  })

  return request<FinancialSummary>(`/analytics/summary?${params}`)
}
