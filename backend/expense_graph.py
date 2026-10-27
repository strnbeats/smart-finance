from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.expense_agent import analyze_expenses


class ExpenseAnalysisState(TypedDict):
    summary: dict
    analysis: str
    validation_errors: list[str]


def analyze_node(state: ExpenseAnalysisState) -> dict:
    """Передаёт финансовую сводку существующему AI-аналитику."""
    analysis = analyze_expenses(state["summary"])

    return {
        "analysis": analysis,
    }


def validate_node(state: ExpenseAnalysisState) -> dict:
    """Проверяет арифметическую согласованность данных и ответ AI."""
    summary = state["summary"]
    errors = []

    income = summary.get("total_income")
    expenses = summary.get("total_expenses")
    balance = summary.get("balance")

    if (
        isinstance(income, (int, float))
        and not isinstance(income, bool)
        and isinstance(expenses, (int, float))
        and not isinstance(expenses, bool)
        and isinstance(balance, (int, float))
        and not isinstance(balance, bool)
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

    return {
        "validation_errors": errors,
    }


def build_expense_graph():
    """Создаёт и компилирует граф анализа расходов."""
    graph = StateGraph(ExpenseAnalysisState)

    graph.add_node("analyze", analyze_node)
    graph.add_node("validate", validate_node)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "validate")
    graph.add_edge("validate", END)

    return graph.compile()


expense_graph = build_expense_graph()


def run_expense_graph(summary: dict) -> dict:
    """Запускает граф и возвращает его итоговое состояние."""
    return expense_graph.invoke(
        {
            "summary": summary,
            "analysis": "",
            "validation_errors": [],
        }
    )
