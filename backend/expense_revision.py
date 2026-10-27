
import json

from backend.llm_client import GigaChatClient


def build_revision_prompt(
    summary: dict,
    analysis: str,
    feedback: str,
) -> str:
    """Формирует запрос на исправление финансового отчёта."""

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
Ты исправляешь финансовый отчёт приложения Smart Finance.

## Исходные данные
{json.dumps(data, ensure_ascii=False, indent=2)}

## Текущий отчёт
{analysis}

## Замечания ревьюера
{feedback}

## Правила
1. Исправь только те проблемы, которые подтверждаются исходными данными.
2. Не добавляй факты о пользователе, которых нет в исходных данных.
3. Не придумывай покупки, привычки, цели или обстоятельства.
4. Не делай выводы о динамике, если нет данных за несколько периодов.
5. Если замечание ревьюера не подтверждается исходными данными,
   не вноси изменение только ради этого замечания.
6. Сохрани полезные выводы исходного отчёта, если они корректны.
7. Не упоминай внутреннюю работу агентов и процесс проверки.
8. Верни только готовый исправленный отчёт на русском языке.
""".strip()


def revise_expense_analysis(
    summary: dict,
    analysis: str,
    feedback: str,
) -> str:
    """Исправляет отчёт по замечаниям ревьюера."""

    if not analysis.strip():
        raise ValueError("Нельзя исправить пустой отчёт.")

    if not feedback.strip():
        raise ValueError("Для исправления нужны замечания ревьюера.")

    client = GigaChatClient()
    prompt = build_revision_prompt(summary, analysis, feedback)
    revised_analysis = client.ask(prompt)

    if not isinstance(revised_analysis, str) or not revised_analysis.strip():
        raise ValueError("Агент исправления вернул пустой отчёт.")

    return revised_analysis.strip()
