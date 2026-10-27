from backend import expense_graph


def make_summary():
    return {
        "total_income": 50000,
        "total_expenses": 15000,
        "balance": 35000,
        "expenses_by_category": {"Еда": 10000, "Транспорт": 5000},
        "transactions_count": 3,
    }


def test_graph_runs_analysis_and_validates_result(monkeypatch):
    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "Расходы на еду — основная категория.",
    )

    result = expense_graph.run_expense_graph(make_summary())

    assert result["analysis"] == "Расходы на еду — основная категория."
    assert result["validation_errors"] == []


def test_graph_detects_incorrect_balance(monkeypatch):
    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "Тестовый отчёт.",
    )

    summary = make_summary()
    summary["balance"] = 12345

    result = expense_graph.run_expense_graph(summary)

    assert any(
        "Баланс не совпадает" in error
        for error in result["validation_errors"]
    )


def test_graph_detects_empty_analysis(monkeypatch):
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
