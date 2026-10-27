from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.expense_agent import analyze_expenses
from backend.expense_reviewer import review_expense_analysis
from backend.expense_revision import revise_expense_analysis


MAX_REVISIONS = 1


class ExpenseAnalysisState(TypedDict):
    summary: dict
    analysis: str
    review_result: dict
    revision_count: int
    validation_errors: list[str]


def analyze_node(state: ExpenseAnalysisState) -> dict:
    """Создаёт первоначальный финансовый отчёт."""
    analysis = analyze_expenses(state["summary"])
    return {"analysis": analysis}


def review_node(state: ExpenseAnalysisState) -> dict:
    """Передаёт отчёт независимому AI-ревьюеру."""
    review_result = review_expense_analysis(
        state["summary"],
        state["analysis"],
    )
    return {"review_result": review_result}


def route_after_review(state: ExpenseAnalysisState) -> str:
    """Решает, нужна ли доработка отчёта."""
    review_result = state.get("review_result", {})

    if (
        isinstance(review_result, dict)
        and review_result.get("status") == "revise"
        and state.get("revision_count", 0) < MAX_REVISIONS
    ):
        return "revise"

    return "validate"


def revise_node(state: ExpenseAnalysisState) -> dict:
    """Исправляет отчёт по замечаниям ревьюера."""
    review_result = state["review_result"]
    feedback = review_result.get("feedback", "")

    revised_analysis = revise_expense_analysis(
        state["summary"],
        state["analysis"],
        feedback,
    )

    return {
        "analysis": revised_analysis,
        "revision_count": state["revision_count"] + 1,
    }


def validate_node(state: ExpenseAnalysisState) -> dict:
    """Проверяет арифметику и результаты работы агентов."""
    summary = state["summary"]
    errors = []

    income = summary.get("total_income")
    expenses = summary.get("total_expenses")
    balance = summary.get("balance")

    numeric_values = (income, expenses, balance)

    if all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in numeric_values
    ):
        if income - expenses != balance:
            errors.append(
                "Баланс не совпадает с разницей доходов и расходов."
            )
    else:
        errors.append(
            "Не удалось проверить баланс: отсутствуют числовые данные."
        )

    analysis = state.get("analysis")
    if not isinstance(analysis, str) or not analysis.strip():
        errors.append("AI-аналитик вернул пустой отчёт.")

    review_result = state.get("review_result")
    valid_statuses = {"approved", "revise", "insufficient_data"}

    if not isinstance(review_result, dict):
        errors.append("AI-ревьюер вернул результат неверного формата.")
    elif (
        review_result.get("status") not in valid_statuses
        or not isinstance(review_result.get("feedback"), str)
        or not review_result["feedback"].strip()
    ):
        errors.append("AI-ревьюер вернул некорректный результат.")

    return {"validation_errors": errors}


def build_expense_graph():
    """Создаёт граф анализа, ревью, доработки и проверки."""
    graph = StateGraph(ExpenseAnalysisState)

    graph.add_node("analyze", analyze_node)
    graph.add_node("review", review_node)
    graph.add_node("revise", revise_node)
    graph.add_node("validate", validate_node)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "review")

    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "revise": "revise",
            "validate": "validate",
        },
    )

    graph.add_edge("revise", "review")
    graph.add_edge("validate", END)

    return graph.compile()


expense_graph = build_expense_graph()


def run_expense_graph(summary: dict) -> dict:
    """Запускает граф и возвращает итоговое состояние."""
    return expense_graph.invoke(
        {
            "summary": summary,
            "analysis": "",
            "review_result": {},
            "revision_count": 0,
            "validation_errors": [],
        }
    )