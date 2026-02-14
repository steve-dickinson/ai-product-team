"""Mission Control Dashboard — real-time monitoring and control.

Launch with:
    uv run streamlit run src/dashboard/app.py
"""

from __future__ import annotations

import asyncio

import streamlit as st

st.set_page_config(
    page_title="AI R&D Team — Mission Control",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 AI Product R&D Team — Mission Control")

with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("▶️ Start New Session", use_container_width=True):
        st.session_state["status"] = "running"
        st.success("Session started!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏸️ Pause", use_container_width=True):
            st.session_state["status"] = "paused"
            st.warning("Paused")
    with col2:
        if st.button("▶️ Resume", use_container_width=True):
            st.session_state["status"] = "running"
            st.info("Resumed")

    if st.button("🛑 KILL SWITCH", type="primary", use_container_width=True):
        st.session_state["status"] = "killed"
        st.error("KILLED — Emergency stop activated")

    st.divider()
    st.header("📊 Budget")
    budget = st.number_input("Session budget ($)", value=15.0, min_value=1.0, max_value=100.0)
    st.metric("Spent", "$0.00", delta=f"-${budget:.2f} remaining")

    st.divider()
    status = st.session_state.get("status", "idle")
    status_colours = {"idle": "🔵", "running": "🟢", "paused": "🟡", "killed": "🔴"}
    st.header(f"Status: {status_colours.get(status, '⚪')} {status.upper()}")

tab_pipeline, tab_feed, tab_costs, tab_learning, tab_graveyard = st.tabs([
    "📋 Pipeline", "💬 Live Feed", "💰 Costs", "🧠 Learning", "💀 Graveyard",
])

with tab_pipeline:
    st.subheader("Pipeline Progress")

    phases = [
        ("Ideation", "✅" if st.session_state.get("phase_1_done") else "⏳"),
        ("Market Research", "⬜"),
        ("Feasibility", "⬜"),
        ("Product Design", "⬜"),
        ("Prototyping", "⬜"),
        ("Testing", "⬜"),
        ("Viability", "⬜"),
    ]

    cols = st.columns(len(phases))
    for col, (name, icon) in zip(cols, phases):
        with col:
            st.markdown(f"### {icon}")
            st.caption(name)

    st.divider()
    st.subheader("Active Ideas")
    st.info("Run a session to see ideas progress through the pipeline.")


with tab_feed:
    st.subheader("Agent Conversation Feed")
    st.caption("Messages appear here in real time during a session.")

    demo_messages = [
        {"agent": "🔵 Visionary", "content": "I've generated 5 product ideas focusing on developer tools."},
        {"agent": "🟡 Judge", "content": "Evaluating... 3 of 5 ideas pass the novelty gate."},
        {"agent": "🔴 Architect", "content": "Idea #2 has a critical dependency on a deprecated API."},
        {"agent": "🟢 Orchestrator", "content": "Moving 3 ideas to Market Research phase."},
    ]

    for msg in demo_messages:
        with st.chat_message(msg["agent"]):
            st.write(msg["content"])


with tab_costs:
    st.subheader("Cost Breakdown")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Spent", "$0.00")
    with col2:
        st.metric("API Calls", "0")
    with col3:
        st.metric("Avg Cost/Call", "$0.00")

    st.divider()
    st.subheader("Cost by Agent")
    st.bar_chart({"Visionary": 0, "Researcher": 0, "Architect": 0, "Judge": 0})

    st.subheader("Cost by Phase")
    st.bar_chart({"Ideation": 0, "Research": 0, "Feasibility": 0})


with tab_learning:
    st.subheader("Institutional Memory")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lessons Learned", "0")
    with col2:
        st.metric("Validated", "0")
    with col3:
        st.metric("Sessions Completed", "0")

    st.divider()
    st.subheader("Recent Lessons")
    st.info("Lessons from past sessions will appear here as the system learns.")

    st.subheader("Failure Trend Analysis")
    st.caption("Patterns across failed concepts — helps identify systemic issues.")


with tab_graveyard:
    st.subheader("💀 Concept Graveyard")
    st.caption("Failed concepts archived with full failure analysis and resurrection conditions.")

    st.info(
        "The graveyard isn't a dump — it's a research database. "
        "Future sessions query it to avoid repeating mistakes and "
        "check if market conditions have changed enough to revive a concept."
    )

    st.dataframe({
        "Concept": ["AI Email Writer Pro", "Universal API Monitor"],
        "Failed At": ["Ideation", "Feasibility"],
        "Reason": ["market_saturated", "technical_blocker"],
        "Score": [4, 5],
        "Resurrection Condition": [
            "Major competitor exits market",
            "OS-level API monitoring becomes standardised",
        ],
    })
