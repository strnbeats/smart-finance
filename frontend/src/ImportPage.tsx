import { useState, type ChangeEvent, type FormEvent } from 'react'
import {
  createTransaction,
  uploadSberPdf,
  type SberPdfPreview,
  type TransactionInput,
} from './api'
import './ImportPage.css'

const formatMoney = (kopecks: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 2,
  }).format(kopecks / 100)

const today = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function ImportPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<SberPdfPreview | null>(null)
  const [form, setForm] = useState<TransactionInput | null>(null)
  const [learnCategoryRule, setLearnCategoryRule] = useState(false)
  const [isParsing, setIsParsing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null

    setFile(selected)
    setPreview(null)
    setForm(null)
    setLearnCategoryRule(false)
    setError('')
    setSuccess('')

    if (selected && !selected.name.toLowerCase().endsWith('.pdf')) {
      setFile(null)
      setError('Выбери файл в формате PDF.')
    }

    if (selected && selected.size > 10 * 1024 * 1024) {
      setFile(null)
      setError('Размер PDF не должен превышать 10 МБ.')
    }
  }

  async function handleParse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!file) {
      setError('Сначала выбери PDF-файл.')
      return
    }

    setIsParsing(true)
    setError('')
    setSuccess('')
    setPreview(null)
    setForm(null)
    setLearnCategoryRule(false)

    try {
      const result = await uploadSberPdf(file)

      setPreview(result)
      setForm({
        ...result.transaction,
        date: result.transaction.date || today(),
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Не удалось распознать PDF.',
      )
    } finally {
      setIsParsing(false)
    }
  }

  function updateField<K extends keyof TransactionInput>(
    field: K,
    value: TransactionInput[K],
  ) {
    setForm((current) =>
      current ? { ...current, [field]: value } : current,
    )
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!form) return

    if (!form.date || !form.category.trim() || !form.description.trim()) {
      setError('Заполни дату, категорию и описание.')
      return
    }

    if (!Number.isSafeInteger(form.amount) || form.amount <= 0) {
      setError('Сумма должна быть положительным числом в копейках.')
      return
    }

    setIsSaving(true)
    setError('')
    setSuccess('')

    try {
      const result = await createTransaction({
        ...form,
        category: form.category.trim(),
        description: form.description.trim(),
        learn_category_rule: learnCategoryRule,
      })

      if (learnCategoryRule && result.category_rule_saved) {
        setSuccess(
          `Операция сохранена. Категория «${form.category.trim()}» запомнена для этого магазина.`,
        )
      } else if (learnCategoryRule) {
        setSuccess(
          'Операция сохранена, но не удалось определить магазин для запоминания категории.',
        )
      } else {
        setSuccess('Операция сохранена в базе данных.')
      }

      setFile(null)
      setPreview(null)
      setForm(null)
      setLearnCategoryRule(false)

      const input = document.getElementById(
        'sber-pdf-file',
      ) as HTMLInputElement | null

      if (input) input.value = ''
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Не удалось сохранить операцию.',
      )
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="import-page">
      <div className="import-intro">
        <div className="import-eyebrow">ИМПОРТ ТРАНЗАКЦИЙ</div>
        <h2>Загрузка банковской выписки</h2>
        <p>
          Загрузи PDF-чек Сбербанка. Проверь распознанные данные
          перед сохранением в финансовую историю.
        </p>
      </div>

      <form className="import-upload-card" onSubmit={handleParse}>
        <div className="upload-symbol">↑</div>
        <h3>Выбери PDF-файл</h3>
        <p>Формат PDF, размер не более 10 МБ</p>

        <label className="file-picker" htmlFor="sber-pdf-file">
          Выбрать файл
        </label>
        <input
          id="sber-pdf-file"
          className="file-input"
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
        />

        <div className="selected-file">
          {file ? file.name : 'Файл ещё не выбран'}
        </div>

        <button
          className="import-primary-button"
          type="submit"
          disabled={!file || isParsing}
        >
          {isParsing ? 'Распознаём...' : 'Распознать операцию'}
        </button>
      </form>

      {error && (
        <div className="import-message import-error" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="import-message import-success" role="status">
          {success}
          <p>
            Чтобы увидеть обновлённые показатели, вернись в обзор
            и обнови страницу.
          </p>
        </div>
      )}

      {preview && form && (
        <form className="import-preview-card" onSubmit={handleSave}>
          <div className="preview-heading">
            <div>
              <div className="import-eyebrow">ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР</div>
              <h3>Проверь данные операции</h3>
            </div>
            <span className="preview-status">Не сохранено</span>
          </div>

          <p className="preview-notice">{preview.message}</p>

          {preview.category_source === 'learned_rule' && (
            <p className="preview-notice">
              Категория предложена по ранее сохранённому правилу магазина.
              Проверь её перед сохранением.
            </p>
          )}

          {preview.category_source === 'mcc' && (
            <p className="preview-notice">
              Категория определена по MCC-коду, если он доступен.
            </p>
          )}

          <label className="import-field">
            Дата
            <input
              type="date"
              value={form.date}
              required
              onChange={(event) => updateField('date', event.target.value)}
            />
          </label>

          <label className="import-field">
            Сумма, ₽
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount / 100}
              required
              onChange={(event) => {
                const value = Number(event.target.value)
                updateField(
                  'amount',
                  Number.isFinite(value) ? Math.round(value * 100) : 0,
                )
              }}
            />
          </label>

          <label className="import-field">
            Тип операции
            <select
              value={form.type}
              onChange={(event) =>
                updateField(
                  'type',
                  event.target.value as TransactionInput['type'],
                )
              }
            >
              <option value="expense">Расход</option>
              <option value="income">Доход</option>
            </select>
          </label>

          <label className="import-field">
            Категория
            <input
              value={form.category}
              required
              onChange={(event) => updateField('category', event.target.value)}
            />
          </label>

          <label className="import-field">
            Описание
            <input
              value={form.description}
              required
              onChange={(event) =>
                updateField('description', event.target.value)
              }
            />
          </label>

          {preview.merchant_key && (
            <label className="import-field">
              <span>
                <input
                  type="checkbox"
                  checked={learnCategoryRule}
                  onChange={(event) =>
                    setLearnCategoryRule(event.target.checked)
                  }
                />
                {' '}Запомнить категорию для этого магазина
              </span>
              <small>
                Магазин: {preview.merchant_key}. В следующий раз приложение
                предложит сохранённую категорию, если MCC-код недоступен.
              </small>
            </label>
          )}

          <div className="preview-total">
            <span>Операция будет сохранена на сумму</span>
            <strong>{formatMoney(form.amount)}</strong>
          </div>

          <button
            className="import-primary-button"
            type="submit"
            disabled={isSaving}
          >
            {isSaving ? 'Сохраняем...' : 'Подтвердить и сохранить'}
          </button>
        </form>
      )}
    </section>
  )
}

export default ImportPage