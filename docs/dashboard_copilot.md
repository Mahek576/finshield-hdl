# FinShield Dashboard Copilot Integration

FinShield includes dashboard integration helpers for the analyst copilot.

The goal is to make the copilot usable inside the Streamlit dashboard while keeping the core logic testable and reusable.

## Purpose

The dashboard copilot layer supports:

- Policy questions
- Transaction explanation
- Retrieved source display
- Guardrail category display
- Dashboard-safe response cards
- Streamlit tab rendering

## Main Module

```text
src/dashboard/copilot_tab.py
Core Functions
FunctionPurpose
dataframe_row_to_recordConverts dashboard dataframe rows into normalized copilot records
select_record_by_transaction_idSelects a transaction from a dataframe
run_copilot_query_for_dashboardRuns a copilot query and returns a display card
build_copilot_cardConverts copilot response into dashboard-friendly structure
format_sources_for_displayFormats retrieved sources
render_copilot_tabStreamlit UI rendering function
Streamlit Usage

A future or existing Streamlit dashboard can import:

from src.dashboard.copilot_tab import render_copilot_tab

Then call:

render_copilot_tab(transactions_df=transactions_df)

If no transaction dataframe is provided, the tab can use a demo transaction record.

Dashboard Modes

The copilot tab supports:

ModePurpose
Policy questionAsk questions about FinShield risk policy, audit policy, and investigation workflow
Explain transactionExplain a selected transaction decision using transaction evidence and retrieved policy context
Safety

The dashboard copilot is advisory only.

It cannot:

Override decisions
Approve blocked transactions
Delete audit evidence
Invent policy
Act as the final fraud authority

Unsafe requests are blocked by the guardrail layer.

Project Value

The dashboard copilot makes FinShield easier to demo.

Dashboard Transaction
        |
        v
Copilot Query
        |
        v
Policy Retrieval + Guardrails
        |
        v
Explanation / Investigation Response
        |
        v
Dashboard Card

This improves product feel, explainability, and MNC-level presentation.
