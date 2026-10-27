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


def test_prompt_contains_financial_summary():
    prompt = expense_agent.build_expense_analysis_prompt(
        make_summary()
    )

    assert "2026-10-01" in prompt
    assert "2026-10-07" in prompt
    assert "kopeks" in prompt

    data = prompt.split("Финансовые данные:\n", 1)[1]
    parsed = json.loads(data)

    assert parsed["total_expenses_kopeks"] == 15000
    assert parsed["total_income_kopeks"] == 50000
    assert parsed["balance_kopeks"] == 35000
    assert parsed["transactions_count"] == 3


def test_prompt_sorts_categories_by_amount():
    prompt = expense_agent.build_expense_analysis_prompt(
        make_summary()
    )

    data = json.loads(
        prompt.split("Финансовые данные:\n", 1)[1]
    )

    categories = data["expenses_by_category"]

    assert categories[0]["category"] == "Еда"
    assert categories[0]["amount_kopeks"] == 10000
    assert categories[0]["share_percent"] == 66.67

    assert categories[1]["category"] == "Транспорт"
    assert categories[1]["amount_kopeks"] == 5000
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
    assert "15000" in calls["prompt"]


def test_prompt_handles_empty_categories():
    prompt = expense_agent.build_expense_analysis_prompt(
        make_summary(
            expenses_by_category={},
        )
    )

    data = json.loads(
        prompt.split("Финансовые данные:\n", 1)[1]
    )

    assert data["expenses_by_category"] == []