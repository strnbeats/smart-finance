from backend import expense_graph


def make_summary():
    return {
        "start_date": "2026-10-01",
        "end_date": "2026-10-31",
        "total_income": 50000,
        "total_expenses": 15000,
        "balance": 35000,
        "expenses_by_category": {
            "Еда": 10000,
            "Транспорт": 5000,
        },
        "transactions_count": 3,
    }


def mock_agents(monkeypatch, review="Существенных проблем не найдено."):
    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "Расходы на еду — основная категория.",
    )
    monkeypatch.setattr(
        expense_graph,
        "review_expense_analysis",
        lambda summary, analysis: review,
    )


def test_graph_runs_analysis_review_and_validation(monkeypatch):
    mock_agents(monkeypatch)

    result = expense_graph.run_expense_graph(make_summary())

    assert result["analysis"] == (
        "Расходы на еду — основная категория."
    )
    assert result["review"] == "Существенных проблем не найдено."
    assert result["validation_errors"] == []


def test_graph_detects_incorrect_balance(monkeypatch):
    mock_agents(monkeypatch)

    summary = make_summary()
    summary["balance"] = 12345

    result = expense_graph.run_expense_graph(summary)

    assert any(
        "Баланс не совпадает" in error
        for error in result["validation_errors"]
    )


def test_graph_detects_empty_analysis(monkeypatch):
    mock_agents(monkeypatch)

    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "   ",
    )

    result = expense_graph.run_expense_graph(make_summary())

    assert any(
        "пустой отчёт" in error
        for error in result["validation_errors"]
    )


def test_graph_detects_empty_review(monkeypatch):
    mock_agents(monkeypatch, review="   ")

    result = expense_graph.run_expense_graph(make_summary())

    assert any(
        "пустой результат проверки" in error
        for error in result["validation_errors"]
    )
