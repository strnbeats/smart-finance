import json

from backend.llm_client import GigaChatClient


def build_expense_review_prompt(summary: dict, analysis: str) -> str:
    """Создаёт запрос для проверки финансового отчёта."""

    data = {
        "period": {
            "start_date": summary.get("start_date"),
            "end_date": summary.get("end_date"),
        },
        "currency": "RUB",
        "total_income_rub": round(summary["total_income"] / 100, 2),
        "total_expenses_rub": round(summary["total_expenses"] / 100, 2),
        "balance_rub": round(summary["balance"] / 100, 2),
        "transactions_count": summary["transactions_count"],
        "expenses_by_category": [
            {
                "category": category,
                "amount_rub": round(amount / 100, 2),
                "share_percent": (
                    round(amount / summary["total_expenses"] * 100, 2)
                    if summary["total_expenses"] > 0
                    else 0
                ),
            }
            for category, amount in summary["expenses_by_category"].items()
        ],
    }

    return f"""
Ты — независимый AI-ревьюер финансовых отчётов приложения Smart Finance.

Твоя задача — проверить отчёт другого AI-аналитика по исходным данным.

## Исходные финансовые данные

{json.dumps(data, ensure_ascii=False, indent=2)}

## Отчёт аналитика

{analysis}

## Правила проверки

1. Сверяй утверждения отчёта только с исходными данными.
2. Ищи неверные суммы, проценты, названия категорий и другие
   противоречия с переданной сводкой.
3. Отмечай выдуманные покупки, привычки, подписки, долги,
   финансовые цели и обстоятельства пользователя.
4. Проверяй, не называет ли аналитик расходы проблемными
   без информации о бюджете и потребностях.
5. Проверяй, не делает ли аналитик выводы о динамике расходов,
   хотя передан только один период.
6. Не считай предположение фактом.
7. Не придумывай замечания ради заполнения ответа.
8. Не переписывай отчёт и не добавляй новые финансовые советы.
9. Если отчёт корректен по доступным данным, явно сообщи об этом.
10. Если данных недостаточно для проверки утверждения, укажи это.

## Формат ответа

### Итог проверки
Один из вариантов: «Существенных проблем не найдено»,
«Есть замечания» или «Недостаточно данных для полной проверки».

### Замечания
Перечисли конкретные проблемы и объясни, с какими исходными
данными они не согласуются. Если проблем нет, так и напиши.

### Что осталось непроверенным
Укажи только существенные ограничения проверки.

Не утверждай, что проверил то, чего нельзя проверить по сводке.
Отвечай по-русски, кратко и конкретно.
""".strip()


def review_expense_analysis(summary: dict, analysis: str) -> str:
    """Передаёт отчёт и финансовую сводку независимому ревьюеру."""

    if not analysis.strip():
        return "Проверка не выполнена: отчёт аналитика пуст."

    client = GigaChatClient()
    prompt = build_expense_review_prompt(summary, analysis)

    return client.ask(prompt)
