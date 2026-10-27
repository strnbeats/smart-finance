from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.expense_agent import analyze_expenses
from backend.expense_reviewer import review_expense_analysis


class ExpenseAnalysisState(TypedDict):
    summary: dict
    analysis: str
    review: str
    validation_errors: list[str]


def analyze_node(state: ExpenseAnalysisState) -> dict:
    """Формирует первоначальный отчёт AI-аналитика."""
    analysis = analyze_expenses(state["summary"])

    return {"analysis": analysis}


def review_node(state: ExpenseAnalysisState) -> dict:
    """Проверяет отчёт независимым AI-ревьюером."""
    review = review_expense_analysis(
        state["summary"],
        state["analysis"],
    )

    return {"review": review}


def validate_node(state: ExpenseAnalysisState) -> dict:
    """Проверяет арифметику и наличие ответов агентов."""
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

    if not isinstance(state.get("analysis"), str) or not state["analysis"].strip():
        errors.append("AI-аналитик вернул пустой отчёт.")

    if not isinstance(state.get("review"), str) or not state["review"].strip():
        errors.append("AI-ревьюер вернул пустой результат проверки.")

    return {"validation_errors": errors}


def build_expense_graph():
    """Создаёт граф анализа, ревью и детерминированной проверки."""
    graph = StateGraph(ExpenseAnalysisState)

    graph.add_node("analyze", analyze_node)
    graph.add_node("review", review_node)
    graph.add_node("validate", validate_node)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "review")
    graph.add_edge("review", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


expense_graph = build_expense_graph()


def run_expense_graph(summary: dict) -> dict:
    """Запускает граф и возвращает итоговое состояние."""
    return expense_graph.invoke(
        {
            "summary": summary,
            "analysis": "",
            "review": "",
            "validation_errors": [],
        }
    )
