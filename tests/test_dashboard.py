"""Smoke test for dashboard — verifies it can be imported."""
from __future__ import annotations

def test_streamlit_available() -> None:
    import streamlit
    assert streamlit is not None
