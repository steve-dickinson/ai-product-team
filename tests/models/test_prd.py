"""Tests for PRD models."""

from __future__ import annotations

import pytest
from src.models.prd import FeatureSpec, Priority, ProductPRD, UserStory


def test_user_story_requires_acceptance_criteria() -> None:
    """User stories must have at least one acceptance criterion."""
    with pytest.raises(Exception):
        UserStory(
            persona="developer",
            action="block distractions",
            benefit="stay focused",
            acceptance_criteria=[],  # Empty — should fail
        )


def test_user_story_auto_generates_id() -> None:
    story = UserStory(
        persona="dev", action="focus", benefit="productivity",
        acceptance_criteria=["Can block sites"],
    )
    assert story.id.startswith("US-")


def test_prd_counts_must_haves() -> None:
    story_must = UserStory(
        persona="dev", action="block", benefit="focus",
        acceptance_criteria=["Works"], priority=Priority.MUST,
    )
    story_could = UserStory(
        persona="dev", action="report", benefit="insight",
        acceptance_criteria=["Shows data"], priority=Priority.COULD,
    )
    feature = FeatureSpec(
        name="Blocking", description="Block sites",
        user_stories=[story_must, story_could], priority=Priority.MUST,
    )
    prd = ProductPRD(
        product_name="Test", problem_statement="Focus",
        vision="Better focus", target_audience="Devs",
        in_scope=["Blocking"], out_of_scope=["Mobile"],
        features=[feature], suggested_tech_stack="Node",
        data_model_overview="Users, Sessions", confidence=0.8,
    )
    assert prd.total_user_stories == 2
    assert prd.must_have_count == 1
