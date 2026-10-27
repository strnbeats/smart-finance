import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import {
  getTransactions,
  getFinancialSummary,
  analyzeExpenses,
  type Transaction,
  type FinancialSummary,
} from './api'

import ImportPage from './ImportPage'
import './App.css'

const formatMoney = (amountInKopecks: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 2,
  }).format(amountInKopecks / 100)

const formatDate = (date: string) => {
  const [year, month, day] = date.split('-').map(Number)

  if (!year || !month || !day) return date

  return new Date(year, month - 1, day).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  })
}

const getCurrentMonthRange = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')

  return {
    start: `${year}-${month}-01`,
    end: `${year}-${month}-${day}`,
  }
}

const navigation = [
  { label: 'Обзор', icon: '◫' },
  { label: 'Транзакции', icon: '⇄' },
  { label: 'Аналитика', icon: '▥' },
  { label: 'Импорт документов', icon: '⇧' },
]

const chartColors = [
  '#70e5b7',
  '#7da8ff',
  '#e99aa4',
  '#c5a3ff',
  '#f3c969',
  '#64c7d9',
  '#f5a66b',
  '#a6d67a',
]

function App() {
  const [activePage, setActivePage] = useState('Обзор')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [summary, setSummary] = useState<FinancialSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [summaryError, setSummaryError] = useState('')

  const initialRange = getCurrentMonthRange()

  const [aiStartDate, setAiStartDate] = useState(initialRange.start)
  const [aiEndDate, setAiEndDate] = useState(initialRange.end)
  const [aiAnalysis, setAiAnalysis] = useState('')
  const [aiError, setAiError] = useState('')
  const [isAiLoading, setIsAiLoading] = useState(false)

  useEffect(() => {
    let isActive = true

    async function loadData() {
      const { start, end } = getCurrentMonthRange()

      setIsLoading(true)
      setError('')
      setSummaryError('')

      const transactionsRequest = getTransactions()
        .then((data) => {
          if (isActive) setTransactions(data)
        })
        .catch((err: unknown) => {
          if (isActive) {
            setError(
              err instanceof Error
                ? err.message
                : 'Не удалось загрузить транзакции',
            )
          }
        })

      const summaryRequest = getFinancialSummary(start, end)
        .then((data) => {
          if (isActive) setSummary(data)
        })
        .catch((err: unknown) => {
          if (isActive) {
            setSummaryError(
              err instanceof Error
                ? err.message
                : 'Не удалось загрузить финансовую сводку',
            )
          }
        })

      await Promise.all([transactionsRequest, summaryRequest])

      if (isActive) setIsLoading(false)
    }

    void loadData()

    return () => {
      isActive = false
    }
  }, [])

  async function handleAnalyzeExpenses() {
    if (!aiStartDate || !aiEndDate) {
      setAiError('Выбери начальную и конечную даты.')
      return
    }

    if (aiStartDate > aiEndDate) {
      setAiError('Начальная дата не может быть позже конечной.')
      return
    }

    setIsAiLoading(true)
    setAiError('')
    setAiAnalysis('')

    try {
      const result = await analyzeExpenses(aiStartDate, aiEndDate)
      setAiAnalysis(result.analysis)
    } catch (err: unknown) {
      setAiError(
        err instanceof Error
          ? err.message
          : 'Не удалось выполнить AI-анализ.',
      )
    } finally {
      setIsAiLoading(false)
    }
  }

  const transactionIncome = transactions
    .filter((transaction) => transaction.type === 'income')
    .reduce((sum, transaction) => sum + transaction.amount, 0)

  const transactionExpenses = transactions
    .filter((transaction) => transaction.type === 'expense')
    .reduce((sum, transaction) => sum + transaction.amount, 0)

  const income = summary?.total_income ?? transactionIncome
  const expenses = summary?.total_expenses ?? transactionExpenses
  const balance = summary?.balance ?? income - expenses

  const recentTransactions = [...transactions]
    .sort(
      (a, b) => b.date.localeCompare(a.date) || b.id - a.id,
    )
    .slice(0, 5)

  const categoryEntries = Object.entries(
    summary?.expenses_by_category ?? {},
  ).sort((a, b) => b[1] - a[1])

  const categoryTotal = categoryEntries.reduce(
    (sum, [, amount]) => sum + amount,
    0,
  )

  let currentAngle = 0

  const chartGradient =
    categoryTotal > 0
      ? `conic-gradient(${categoryEntries
          .map(([, amount], index) => {
            const start = currentAngle
            currentAngle += (amount / categoryTotal) * 360

            return `${chartColors[index % chartColors.length]} ${start}deg ${currentAngle}deg`
          })
          .join(', ')})`
      : '#273142'

  const monthLabel = new Date().toLocaleDateString('ru-RU', {
    month: 'long',
    year: 'numeric',
  })

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">S</div>
          <div>
            <div className="brand-name">smart finance</div>
            <div className="brand-caption">PERSONAL FINANCE</div>
          </div>
        </div>

        <div className="nav-caption">МЕНЮ</div>

        <nav className="navigation">
          {navigation.map((item) => (
            <button
              className={`nav-item ${activePage === item.label ? 'active' : ''}`}
              key={item.label}
              onClick={() => setActivePage(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>

              {item.label === 'Импорт документов' && (
                <span className="nav-badge">PDF</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="status-indicator" />
          <div>
            <div className="status-title">Локальный режим</div>
            <div className="status-caption">
              Данные на вашем устройстве
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Smart Finance / {activePage}
            </div>
            <h1>{activePage}</h1>
          </div>

          <div className="profile">
            <div className="profile-avatar">SF</div>
            <div>
              <div className="profile-name">Мои финансы</div>
              <div className="profile-caption">Личный кабинет</div>
            </div>
          </div>
        </header>

        {activePage === 'Обзор' ? (
          <>
            <section className="welcome-row">
              <div>
                <h2>Финансовая сводка</h2>
                <p>Вот как обстоят дела с твоими деньгами.</p>
              </div>

              <span className="period-label">{monthLabel}</span>
            </section>

            {error && (
              <div role="alert" className="error-message">
                <strong>Не удалось загрузить транзакции.</strong>
                <p>{error}</p>
                <button
                  className="primary-button"
                  onClick={() => window.location.reload()}
                >
                  Попробовать снова
                </button>
              </div>
            )}

            {summaryError && (
              <div role="alert" className="error-message">
                <strong>Не удалось загрузить аналитику.</strong>
                <p>{summaryError}</p>
              </div>
            )}

            <section className="summary-grid">
              <article className="summary-card balance-card">
                <div className="card-topline">
                  <span>Общий баланс за месяц</span>
                  <span className="card-icon">₽</span>
                </div>

                <div className="balance-amount">
                  {isLoading ? 'Загрузка...' : formatMoney(balance)}
                </div>

                <div className="card-footnote">
                  <span className="trend-positive">↗</span>
                  Доходы минус расходы
                </div>

                <div className="balance-decoration" />
              </article>

              <article className="summary-card">
                <div className="card-topline">
                  <span>Доходы</span>
                  <span className="card-icon income-icon">↙</span>
                </div>

                <div className="summary-amount">
                  {isLoading ? 'Загрузка...' : formatMoney(income)}
                </div>

                <div className="card-footnote">За текущий месяц</div>
              </article>

              <article className="summary-card">
                <div className="card-topline">
                  <span>Расходы</span>
                  <span className="card-icon expense-icon">↗</span>
                </div>

                <div className="summary-amount">
                  {isLoading ? 'Загрузка...' : formatMoney(expenses)}
                </div>

                <div className="card-footnote">За текущий месяц</div>
              </article>
            </section>

            <section
              className="panel"
              style={{ marginBottom: 24 }}
            >
              <div className="panel-heading">
                <div>
                  <h3>AI-анализ расходов</h3>
                  <p>
                    Персональные наблюдения и рекомендации на основе
                    финансовой сводки
                  </p>
                </div>
                <span className="card-icon">✦</span>
              </div>

              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 12,
                  alignItems: 'end',
                  marginBottom: 20,
                }}
              >
                <label
                  style={{
                    display: 'grid',
                    gap: 7,
                    flex: '1 1 160px',
                  }}
                >
                  <span>Начало периода</span>
                  <input
                    type="date"
                    value={aiStartDate}
                    onChange={(event) =>
                      setAiStartDate(event.target.value)
                    }
                    max={aiEndDate || undefined}
                    style={{
                      padding: 12,
                      borderRadius: 10,
                      border: '1px solid #303b4e',
                      background: '#111724',
                      color: '#fff',
                      minWidth: 0,
                    }}
                  />
                </label>

                <label
                  style={{
                    display: 'grid',
                    gap: 7,
                    flex: '1 1 160px',
                  }}
                >
                  <span>Конец периода</span>
                  <input
                    type="date"
                    value={aiEndDate}
                    onChange={(event) =>
                      setAiEndDate(event.target.value)
                    }
                    min={aiStartDate || undefined}
                    style={{
                      padding: 12,
                      borderRadius: 10,
                      border: '1px solid #303b4e',
                      background: '#111724',
                      color: '#fff',
                      minWidth: 0,
                    }}
                  />
                </label>

                <button
                  className="primary-button"
                  onClick={handleAnalyzeExpenses}
                  disabled={isAiLoading}
                >
                  {isAiLoading
                    ? 'Анализируем...'
                    : '✦ Проанализировать'}
                </button>
              </div>

              {isAiLoading && (
                <p role="status">
                  AI-помощник анализирует финансовую сводку...
                </p>
              )}

              {aiError && (
                <div role="alert" className="error-message">
                  <strong>Не удалось выполнить анализ</strong>
                  <p>{aiError}</p>
                  <button
                    className="text-button"
                    onClick={handleAnalyzeExpenses}
                    disabled={isAiLoading}
                  >
                    Попробовать снова
                  </button>
                </div>
              )}

              {aiAnalysis && !isAiLoading && (
                <div
                  className="insight-box"
                  style={{
                    alignItems: 'flex-start',
                    marginTop: 12,
                  }}
                >
                  <span className="insight-icon">✦</span>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="insight-title">
                      Результат анализа
                    </div>

                    <div className="ai-markdown">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                      >
                        {aiAnalysis
                          .replace(/\\\|/g, '|')
                          .replace(/\u202f/g, ' ')}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )}

              {!aiAnalysis && !aiError && !isAiLoading && (
                <p
                  style={{
                    color: '#8590a4',
                    fontSize: 13,
                  }}
                >
                  Выбери период и запусти анализ. Рекомендации появятся
                  здесь.
                </p>
              )}
            </section>

            <section className="content-grid">
              <article className="panel transactions-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Последние операции</h3>
                    <p>Транзакции из твоей базы данных</p>
                  </div>

                  <button
                    className="text-button"
                    onClick={() => setActivePage('Транзакции')}
                  >
                    Все операции →
                  </button>
                </div>

                <div className="transaction-list">
                  {isLoading ? (
                    <p>Загружаем транзакции...</p>
                  ) : error ? (
                    <p>Список временно недоступен.</p>
                  ) : recentTransactions.length === 0 ? (
                    <p>Пока нет транзакций.</p>
                  ) : (
                    recentTransactions.map((transaction) => (
                      <div
                        className="transaction-row"
                        key={transaction.id}
                      >
                        <div
                          className={`transaction-icon ${
                            transaction.type === 'income'
                              ? 'transaction-income'
                              : ''
                          }`}
                        >
                          {transaction.type === 'income' ? '↙' : '↗'}
                        </div>

                        <div className="transaction-info">
                          <div className="transaction-title">
                            {transaction.description || transaction.category}
                          </div>

                          <div className="transaction-meta">
                            {transaction.category} · {formatDate(transaction.date)}
                          </div>
                        </div>

                        <div
                          className={`transaction-amount ${
                            transaction.type === 'income'
                              ? 'amount-income'
                              : ''
                          }`}
                        >
                          {transaction.type === 'income' ? '+' : '−'}
                          {formatMoney(transaction.amount)}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </article>

              <article className="panel spending-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Расходы по категориям</h3>
                    <p>Распределение трат за текущий месяц</p>
                  </div>
                </div>

                {isLoading ? (
                  <p>Загружаем аналитику...</p>
                ) : summaryError ? (
                  <p>Диаграмма временно недоступна.</p>
                ) : categoryEntries.length === 0 || categoryTotal === 0 ? (
                  <p>За этот месяц расходов пока нет.</p>
                ) : (
                  <>
                    <div
                      role="img"
                      aria-label="Круговая диаграмма расходов по категориям"
                      style={{
                        width: 190,
                        height: 190,
                        maxWidth: '100%',
                        margin: '0 auto 22px',
                        borderRadius: '50%',
                        background: chartGradient,
                        position: 'relative',
                        display: 'grid',
                        placeItems: 'center',
                      }}
                    >
                      <div
                        style={{
                          width: 118,
                          height: 118,
                          borderRadius: '50%',
                          background: '#111724',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: 5,
                        }}
                      >
                        <span
                          style={{ color: '#8590a4', fontSize: 11 }}
                        >
                          Всего
                        </span>

                        <strong
                          style={{
                            fontSize: 16,
                            textAlign: 'center',
                          }}
                        >
                          {formatMoney(categoryTotal)}
                        </strong>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gap: 13 }}>
                      {categoryEntries.map(([category, amount], index) => {
                        const percentage = (amount / categoryTotal) * 100

                        return (
                          <div
                            key={category}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 9,
                              fontSize: 11,
                            }}
                          >
                            <span
                              style={{
                                width: 9,
                                height: 9,
                                flexShrink: 0,
                                borderRadius: '50%',
                                background:
                                  chartColors[index % chartColors.length],
                              }}
                            />

                            <span
                              style={{
                                color: '#aab4c5',
                                flex: 1,
                                minWidth: 0,
                                overflowWrap: 'anywhere',
                              }}
                            >
                              {category}
                            </span>

                            <span style={{ color: '#8590a4' }}>
                              {percentage.toLocaleString('ru-RU', {
                                maximumFractionDigits: 1,
                              })}
                              %
                            </span>

                            <strong style={{ whiteSpace: 'nowrap' }}>
                              {formatMoney(amount)}
                            </strong>
                          </div>
                        )
                      })}
                    </div>
                  </>
                )}
              </article>
            </section>

            <footer className="page-footer">
              Smart Finance <span>·</span> Аналитика из FastAPI
            </footer>
          </>
        ) : activePage === 'Импорт документов' ? (
          <ImportPage />
        ) : (
          <section className="panel placeholder-panel">
            <div className="placeholder-icon">
              {navigation.find((item) => item.label === activePage)?.icon}
            </div>

            <h2>{activePage}</h2>

            <p>
              Этот раздел пока в разработке. Следующим шагом подключим его
              к FastAPI и базе данных.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App