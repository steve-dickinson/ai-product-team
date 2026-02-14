"""Smoke test — verifies the project structure is correct."""


def test_imports_work() -> None:
    """Verify all source packages are importable."""
    import src.agents
    import src.core
    import src.models
    import src.storage
    import src.tools

    assert True


def test_pydantic_ai_available() -> None:
    """Verify pydantic-ai is installed and importable."""
    from pydantic_ai import Agent

    assert Agent is not None
