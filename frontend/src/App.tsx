import { useEffect, useState } from 'react'
import { getTransactions, type Transaction } from './api'
import './App.css'

const formatMoney = (amountInKopecks: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(amountInKopecks / 100)

const formatDate = (date: string) => {
  const [year, month, day] = date.split('-').map(Number)

  if (!year || !month || !day) return date

  return new Date(year, month - 1, day).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  })
}

const navigation = [
  { label: 'Обзор', icon: '◫' },
  { label: 'Транзакции', icon: '⇄' },
  { label: 'Аналитика', icon: '▥' },
  { label: 'Импорт документов', icon: '⇧' },
]

function App() {
  const [activePage, setActivePage] = useState('Обзор')
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isActive = true

    async function loadTransactions() {
      try {
        setIsLoading(true)
        setError('')

        const data = await getTransactions()

        if (isActive) {
          setTransactions(data)
        }
      } catch (err) {
        if (isActive) {
          setError(
            err instanceof Error
              ? err.message
              : 'Не удалось загрузить транзакции',
          )
        }
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    void loadTransactions()

    return () => {
      isActive = false
    }
  }, [])

  const income = transactions
    .filter((transaction) => transaction.type === 'income')
    .reduce((sum, transaction) => sum + transaction.amount, 0)

  const expenses = transactions
    .filter((transaction) => transaction.type === 'expense')
    .reduce((sum, transaction) => sum + transaction.amount, 0)

  const balance = income - expenses

  const recentTransactions = [...transactions]
    .sort((a, b) => b.date.localeCompare(a.date))
    .slice(0, 5)

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
            <div className="status-caption">Данные на вашем устройстве</div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">Smart Finance / {activePage}</div>
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
              <span className="period-label">Данные из базы SQLite</span>
            </section>

            {error && (
              <div
                role="alert"
                style={{
                  padding: '16px',
                  marginBottom: '20px',
                  borderRadius: '12px',
                  background: 'rgba(239, 68, 68, 0.12)',
                  color: '#fca5a5',
                }}
              >
                <strong>Не удалось загрузить данные.</strong>
                <p>{error}</p>
                <button
                  className="primary-button"
                  onClick={() => window.location.reload()}
                >
                  Попробовать снова
                </button>
              </div>
            )}

            <section className="summary-grid">
              <article className="summary-card balance-card">
                <div className="card-topline">
                  <span>Общий баланс</span>
                  <span className="card-icon">₽</span>
                </div>
                <div className="balance-amount">
                  {isLoading ? 'Загрузка...' : formatMoney(balance)}
                </div>
                <div className="card-footnote">
                  <span className="trend-positive">↗</span> Доходы минус расходы
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
                <div className="card-footnote">По загруженным транзакциям</div>
              </article>

              <article className="summary-card">
                <div className="card-topline">
                  <span>Расходы</span>
                  <span className="card-icon expense-icon">↗</span>
                </div>
                <div className="summary-amount">
                  {isLoading ? 'Загрузка...' : formatMoney(expenses)}
                </div>
                <div className="card-footnote">По загруженным транзакциям</div>
              </article>
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
                    <p>Пока нет транзакций. Добавь первую через API.</p>
                  ) : (
                    recentTransactions.map((transaction) => (
                      <div className="transaction-row" key={transaction.id}>
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
                            transaction.type === 'income' ? 'amount-income' : ''
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
                    <h3>Финансовая сводка</h3>
                    <p>Доходы и расходы из базы</p>
                  </div>
                </div>

                <div className="chart">
                  <div className="chart-gridline line-one" />
                  <div className="chart-gridline line-two" />
                  <div className="chart-gridline line-three" />

                  <div className="bar-group">
                    <div
                      className="bar income-bar"
                      style={{
                        height: `${Math.max(
                          4,
                          (income / Math.max(income, expenses, 1)) * 85,
                        )}%`,
                      }}
                    />
                    <div
                      className="bar expense-bar"
                      style={{
                        height: `${Math.max(
                          4,
                          (expenses / Math.max(income, expenses, 1)) * 85,
                        )}%`,
                      }}
                    />
                    <span>Сейчас</span>
                  </div>
                </div>

                <div className="chart-legend">
                  <span>
                    <i className="legend-dot income-dot" /> Доходы
                  </span>
                  <span>
                    <i className="legend-dot expense-dot" /> Расходы
                  </span>
                </div>

                <div className="insight-box">
                  <span className="insight-icon">✦</span>
                  <div>
                    <div className="insight-title">Финансовая подсказка</div>
                    <p>
                      Следующим шагом добавим анализ расходов по категориям и
                      AI-помощника.
                    </p>
                  </div>
                </div>
              </article>
            </section>

            <footer className="page-footer">
              Smart Finance <span>·</span> Данные загружаются из FastAPI
            </footer>
          </>
        ) : (
          <section className="panel placeholder-panel">
            <div className="placeholder-icon">
              {navigation.find((item) => item.label === activePage)?.icon}
            </div>
            <h2>{activePage}</h2>
            <p>
              Этот раздел пока в разработке. Следующим шагом подключим его к
              FastAPI и базе данных.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
