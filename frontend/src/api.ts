const API_URL = 'http://127.0.0.1:8000'

export type TransactionType = 'income' | 'expense'

export type CategorySource = 'mcc' | 'learned_rule' | 'heuristic'

export interface Transaction {
  id: number
  date: string
  amount: number
  type: TransactionType
  category: string
  description: string
  mcc?: string | null
}

export interface FinancialSummary {
  start_date: string
  end_date: string
  total_income: number
  total_expenses: number
  balance: number
  expenses_by_category: Record<string, number>
  transactions_count: number
}

export type TransactionInput = Omit<Transaction, 'id'>

export interface SberPdfPreview {
  saved: false
  message: string
  merchant_key: string | null
  category_source: CategorySource
  transaction: TransactionInput
}

export interface CreateTransactionInput extends TransactionInput {
  learn_category_rule?: boolean
}

export interface CreateTransactionResponse extends Transaction {
  category_rule_saved: boolean
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options)

  if (!response.ok) {
    let message = `Ошибка API: ${response.status}`

    try {
      const body = await response.json()

      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // Если сервер вернул не JSON, используем сообщение по умолчанию.
    }

    throw new Error(message)
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

export function uploadSberPdf(file: File): Promise<SberPdfPreview> {
  const formData = new FormData()
  formData.append('file', file)

  return request<SberPdfPreview>('/imports/sber/pdf', {
    method: 'POST',
    body: formData,
  })
}

export function createTransaction(
  transaction: CreateTransactionInput,
): Promise<CreateTransactionResponse> {
  return request<CreateTransactionResponse>('/transactions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(transaction),
  })
}