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


def mock_agents(monkeypatch, review_result=None):
    if review_result is None:
        review_result = {
            "status": "approved",
            "feedback": "Существенных проблем не найдено.",
        }

    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "Расходы на еду — основная категория.",
    )
    monkeypatch.setattr(
        expense_graph,
        "review_expense_analysis",
        lambda summary, analysis: review_result,
    )
    monkeypatch.setattr(
        expense_graph,
        "revise_expense_analysis",
        lambda summary, analysis, feedback: (
            "Исправленный отчёт без неподтверждённых выводов."
        ),
    )


def test_graph_approves_analysis_without_revision(monkeypatch):
    mock_agents(monkeypatch)

    result = expense_graph.run_expense_graph(make_summary())

    assert result["analysis"] == (
        "Расходы на еду — основная категория."
    )
    assert result["review_result"]["status"] == "approved"
    assert result["revision_count"] == 0
    assert result["validation_errors"] == []


def test_graph_revises_analysis_and_reviews_it_again(monkeypatch):
    review_results = iter(
        [
            {
                "status": "revise",
                "feedback": "Убери неподтверждённые выводы.",
            },
            {
                "status": "approved",
                "feedback": "Существенных проблем не найдено.",
            },
        ]
    )
    review_calls = []
    revision_calls = []

    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "Первоначальный отчёт.",
    )

    def mock_review(summary, analysis):
        review_calls.append(analysis)
        return next(review_results)

    def mock_revision(summary, analysis, feedback):
        revision_calls.append((analysis, feedback))
        return "Исправленный отчёт."

    monkeypatch.setattr(
        expense_graph,
        "review_expense_analysis",
        mock_review,
    )
    monkeypatch.setattr(
        expense_graph,
        "revise_expense_analysis",
        mock_revision,
    )

    result = expense_graph.run_expense_graph(make_summary())

    assert result["analysis"] == "Исправленный отчёт."
    assert result["review_result"]["status"] == "approved"
    assert result["revision_count"] == 1
    assert len(review_calls) == 2
    assert len(revision_calls) == 1
    assert revision_calls[0][1] == "Убери неподтверждённые выводы."
    assert result["validation_errors"] == []


def test_graph_does_not_revise_more_than_once(monkeypatch):
    review_calls = []
    revision_calls = []

    monkeypatch.setattr(
        expense_graph,
        "analyze_expenses",
        lambda summary: "Первоначальный отчёт.",
    )

    def mock_review(summary, analysis):
        review_calls.append(analysis)
        return {
            "status": "revise",
            "feedback": "Есть замечания.",
        }

    def mock_revision(summary, analysis, feedback):
        revision_calls.append(analysis)
        return "Исправленный отчёт."

    monkeypatch.setattr(
        expense_graph,
        "review_expense_analysis",
        mock_review,
    )
    monkeypatch.setattr(
        expense_graph,
        "revise_expense_analysis",
        mock_revision,
    )

    result = expense_graph.run_expense_graph(make_summary())

    assert result["revision_count"] == 1
    assert len(review_calls) == 2
    assert len(revision_calls) == 1
    assert result["review_result"]["status"] == "revise"


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


def test_graph_detects_invalid_review_result(monkeypatch):
    mock_agents(
        monkeypatch,
        review_result={
            "status": "unknown",
            "feedback": "",
        },
    )

    result = expense_graph.run_expense_graph(make_summary())

    assert any(
        "некорректный результат" in error
        for error in result["validation_errors"]
    )