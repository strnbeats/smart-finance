import json

from backend.llm_client import GigaChatClient


def build_expense_analysis_prompt(summary: dict) -> str:
    """Создаёт запрос к модели только на основе агрегированных данных."""
    total_expenses = summary["total_expenses"]
    total_income = summary["total_income"]

    categories = []
    for category, amount in summary["expenses_by_category"].items():
        share = (
            round(amount / total_expenses * 100, 2)
            if total_expenses > 0
            else 0
        )
        categories.append(
            {
                "category": category,
                "amount_kopeks": amount,
                "share_percent": share,
            }
        )

    categories.sort(
        key=lambda item: item["amount_kopeks"],
        reverse=True,
    )

    data = {
        "period": {
            "start_date": summary["start_date"],
            "end_date": summary["end_date"],
        },
        "currency": "RUB",
        "amount_unit": "kopeks",
        "total_income_kopeks": total_income,
        "total_expenses_kopeks": total_expenses,
        "balance_kopeks": summary["balance"],
        "transactions_count": summary["transactions_count"],
        "expenses_by_category": categories,
    }

    return f"""
Ты — AI-аналитик личных финансов в приложении Smart Finance.

Проанализируй предоставленную финансовую сводку и ответь на русском языке.

Правила:
1. Используй только факты из переданных данных.
2. Не придумывай доходы, расходы, покупки, привычки и обстоятельства пользователя.
3. Все денежные суммы во входных данных указаны в копейках.
   Для отображения в рублях раздели сумму на 100.
4. Доли категорий уже рассчитаны программой. Не подменяй их
   выдуманными значениями.
5. Если данных мало, прямо скажи об этом.
6. Не называй расходы проблемными только потому, что они велики:
   у тебя нет информации о потребностях пользователя.
7. Предлагай конкретные способы проверить возможность экономии,
   но не обещай гарантированный результат.
8. Не запрашивай личные или банковские данные.
9. Ответ должен содержать:
   - краткий общий вывод;
   - основные категории расходов;
   - наблюдения, которые действительно следуют из цифр;
   - от двух до четырёх практических рекомендаций, если данных
     достаточно;
   - ограничения анализа, если данных недостаточно.
10. Не выдавай анализ одного периода за доказательство тенденции
    во времени.

Финансовые данные:
{json.dumps(data, ensure_ascii=False, indent=2)}
""".strip()


def analyze_expenses(summary: dict) -> str:
    """Передаёт агрегированную сводку GigaChat и возвращает анализ."""
    if summary["total_expenses"] <= 0:
        return (
            "За выбранный период расходы не зарегистрированы. "
            "Пока недостаточно данных для анализа структуры расходов. "
            "Проверь, что операции за этот период импортированы."
        )

    client = GigaChatClient()
    prompt = build_expense_analysis_prompt(summary)
    return client.ask(prompt)
