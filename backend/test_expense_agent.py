import json

from backend import expense_agent


def make_summary(
    total_expenses=15000,
    total_income=50000,
    expenses_by_category=None,
    transactions_count=3,
):
    if expenses_by_category is None:
        expenses_by_category = {
            "Транспорт": 5000,
            "Еда": 10000,
        }

    return {
        "start_date": "2026-10-01",
        "end_date": "2026-10-07",
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "expenses_by_category": expenses_by_category,
        "transactions_count": transactions_count,
    }


def extract_prompt_data(prompt):
    data = prompt.split("Финансовые данные:\n", 1)[1]
    return json.loads(data)


def test_prompt_contains_financial_summary():
    prompt = expense_agent.build_expense_analysis_prompt(
        make_summary()
    )

    assert "2026-10-01" in prompt
    assert "2026-10-07" in prompt
    assert "amount_rub" in prompt

    data = extract_prompt_data(prompt)

    assert data["currency"] == "RUB"
    assert data["total_expenses_rub"] == 150.0
    assert data["total_income_rub"] == 500.0
    assert data["balance_rub"] == 350.0
    assert data["transactions_count"] == 3


def test_prompt_sorts_categories_by_amount():
    prompt = expense_agent.build_expense_analysis_prompt(
        make_summary()
    )

    data = extract_prompt_data(prompt)
    categories = data["expenses_by_category"]

    assert categories[0]["category"] == "Еда"
    assert categories[0]["amount_rub"] == 100.0
    assert categories[0]["share_percent"] == 66.67

    assert categories[1]["category"] == "Транспорт"
    assert categories[1]["amount_rub"] == 50.0
    assert categories[1]["share_percent"] == 33.33


def test_no_expenses_does_not_call_gigachat(monkeypatch):
    def unexpected_client():
        raise AssertionError(
            "GigaChat не должен вызываться без расходов"
        )

    monkeypatch.setattr(
        expense_agent,
        "GigaChatClient",
        unexpected_client,
    )

    result = expense_agent.analyze_expenses(
        make_summary(
            total_expenses=0,
            expenses_by_category={},
        )
    )

    assert isinstance(result, str)
    assert result


def test_analysis_uses_gigachat_for_expenses(monkeypatch):
    calls = {}

    class FakeGigaChatClient:
        def ask(self, prompt):
            calls["prompt"] = prompt
            return "Тестовый анализ расходов"

    monkeypatch.setattr(
        expense_agent,
        "GigaChatClient",
        FakeGigaChatClient,
    )

    result = expense_agent.analyze_expenses(make_summary())

    assert result == "Тестовый анализ расходов"
    assert "prompt" in calls

    data = extract_prompt_data(calls["prompt"])
    assert data["total_expenses_rub"] == 150.0


def test_prompt_handles_empty_categories():
    prompt = expense_agent.build_expense_analysis_prompt(
        make_summary(
            expenses_by_category={},
        )
    )

    data = extract_prompt_data(prompt)

    assert data["expenses_by_category"] == []