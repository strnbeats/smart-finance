import json

from backend.llm_client import GigaChatClient


def build_expense_review_prompt(summary: dict, analysis: str) -> str:
    """Создаёт запрос для структурированной проверки отчёта."""

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
        "expenses_by_category": {
            category: round(amount / 100, 2)
            for category, amount in summary["expenses_by_category"].items()
        },
    }

    return f"""
Ты — независимый AI-ревьюер финансовых отчётов Smart Finance.

## Исходные данные
{json.dumps(data, ensure_ascii=False, indent=2)}

## Отчёт аналитика
{analysis}

## Проверь
- соответствуют ли суммы и категории исходным данным;
- нет ли выдуманных фактов о пользователе;
- не выдаются ли предположения за факты;
- нет ли выводов о динамике по одному периоду;
- не объявляются ли расходы проблемными без контекста.

Не придумывай замечания ради заполнения ответа.
Если существенных проблем нет, используй статус approved.
Если есть конкретные исправимые проблемы, используй revise.
Если данных недостаточно для полноценной проверки, используй insufficient_data.

Верни только валидный JSON без Markdown и пояснений вокруг него:
{{
  "status": "approved",
  "feedback": "Краткий результат проверки"
}}

Поле status должно содержать ровно одно значение:
approved, revise или insufficient_data.

Поле feedback должно объяснять результат по-русски.
""".strip()


def review_expense_analysis(summary: dict, analysis: str) -> dict:
    """Проверяет отчёт и возвращает статус с замечаниями."""

    if not isinstance(analysis, str) or not analysis.strip():
        return {
            "status": "insufficient_data",
            "feedback": "Проверка невозможна: отчёт аналитика пуст.",
        }

    client = GigaChatClient()
    prompt = build_expense_review_prompt(summary, analysis)
    response = client.ask(prompt)

    try:
        result = json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return {
            "status": "insufficient_data",
            "feedback": (
                "Не удалось разобрать структурированный ответ ревьюера. "
                "Автоматическое решение о доработке не принято."
            ),
        }

    if not isinstance(result, dict):
        return {
            "status": "insufficient_data",
            "feedback": "Ревьюер вернул ответ в неверном формате.",
        }

    status = result.get("status")
    feedback = result.get("feedback")

    if status not in {"approved", "revise", "insufficient_data"}:
        status = "insufficient_data"

    if not isinstance(feedback, str) or not feedback.strip():
        feedback = "Ревьюер не предоставил пояснений."

    return {
        "status": status,
        "feedback": feedback.strip(),
    }
