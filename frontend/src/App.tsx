import { useState } from 'react'
import './App.css'

type Transaction = {
  id: number
  title: string
  category: string
  date: string
  amount: number
  type: 'income' | 'expense'
}

const initialTransactions: Transaction[] = [
  { id: 1, title: 'Зарплата', category: 'Доходы', date: '24 окт.', amount: 85000, type: 'income' },
  { id: 2, title: 'Яндекс Go', category: 'Транспорт', date: '24 окт.', amount: 300, type: 'expense' },
  { id: 3, title: 'Пятёрочка', category: 'Продукты', date: '23 окт.', amount: 1240, type: 'expense' },
  { id: 4, title: 'Подписка Spotify', category: 'Подписки', date: '22 окт.', amount: 299, type: 'expense' },
  { id: 5, title: 'Перевод', category: 'Доходы', date: '21 окт.', amount: 2500, type: 'income' },
]

const formatMoney = (amount: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(amount)

const navigation = [
  { label: 'Обзор', icon: '◫' },
  { label: 'Транзакции', icon: '⇄' },
  { label: 'Аналитика', icon: '▥' },
  { label: 'Импорт документов', icon: '⇧' },
]

function App() {
  const [activePage, setActivePage] = useState('Обзор')
  const [transactions] = useState(initialTransactions)

  const income = transactions
    .filter((transaction) => transaction.type === 'income')
    .reduce((sum, transaction) => sum + transaction.amount, 0)

  const expenses = transactions
    .filter((transaction) => transaction.type === 'expense')
    .reduce((sum, transaction) => sum + transaction.amount, 0)

  const balance = income - expenses

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
              <span className="period-label">Демо-данные · Октябрь 2026</span>
            </section>

            <section className="summary-grid">
              <article className="summary-card balance-card">
                <div className="card-topline">
                  <span>Общий баланс</span>
                  <span className="card-icon">₽</span>
                </div>
                <div className="balance-amount">{formatMoney(balance)}</div>
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
                <div className="summary-amount">{formatMoney(income)}</div>
                <div className="card-footnote">За отображаемый период</div>
              </article>

              <article className="summary-card">
                <div className="card-topline">
                  <span>Расходы</span>
                  <span className="card-icon expense-icon">↗</span>
                </div>
                <div className="summary-amount">{formatMoney(expenses)}</div>
                <div className="card-footnote">За отображаемый период</div>
              </article>
            </section>

            <section className="content-grid">
              <article className="panel transactions-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Последние операции</h3>
                    <p>Твои недавние движения средств</p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => setActivePage('Транзакции')}
                  >
                    Все операции →
                  </button>
                </div>

                <div className="transaction-list">
                  {transactions.map((transaction) => (
                    <div className="transaction-row" key={transaction.id}>
                      <div
                        className={`transaction-icon ${
                          transaction.type === 'income' ? 'transaction-income' : ''
                        }`}
                      >
                        {transaction.type === 'income' ? '↙' : '↗'}
                      </div>
                      <div className="transaction-info">
                        <div className="transaction-title">{transaction.title}</div>
                        <div className="transaction-meta">
                          {transaction.category} · {transaction.date}
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
                  ))}
                </div>
              </article>

              <article className="panel spending-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Расходы и доходы</h3>
                    <p>Сравнение по демо-данным</p>
                  </div>
                </div>

                <div className="chart">
                  <div className="chart-gridline line-one" />
                  <div className="chart-gridline line-two" />
                  <div className="chart-gridline line-three" />
                  <div className="bar-group">
                    <div className="bar income-bar" style={{ height: '85%' }} />
                    <div className="bar expense-bar" style={{ height: '24%' }} />
                    <span>Доходы</span>
                  </div>
                  <div className="bar-group">
                    <div className="bar income-bar" style={{ height: '42%' }} />
                    <div className="bar expense-bar" style={{ height: '18%' }} />
                    <span>Расходы</span>
                  </div>
                  <div className="bar-group">
                    <div className="bar income-bar" style={{ height: '60%' }} />
                    <div className="bar expense-bar" style={{ height: '35%' }} />
                    <span>Баланс</span>
                  </div>
                </div>

                <div className="chart-legend">
                  <span><i className="legend-dot income-dot" /> Доходы</span>
                  <span><i className="legend-dot expense-dot" /> Расходы</span>
                </div>

                <div className="insight-box">
                  <span className="insight-icon">✦</span>
                  <div>
                    <div className="insight-title">Финансовая подсказка</div>
                    <p>После подключения реальных данных здесь появится анализ твоих расходов.</p>
                  </div>
                </div>
              </article>
            </section>

            <footer className="page-footer">
              Smart Finance <span>·</span> Первый прототип интерфейса
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
            {activePage === 'Импорт документов' && (
              <button
                className="primary-button"
                onClick={() =>
                  setActivePage('Импорт документов')
                }
              >
                Подготовить импорт PDF
              </button>
            )}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
