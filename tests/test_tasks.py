"""Task construction, and the two loading contracts Inspect's CLI depends on."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from constitutional_drift.conditions import AUTHORITY, Condition, parse_values
from constitutional_drift.prompts import build_prompt
from constitutional_drift.scoring import CONSTITUTION_PATH
from constitutional_drift.tasks import COMPOSE_FILE, constitution_edit

TASKS_PY = Path(__file__).resolve().parent.parent / "constitutional_drift" / "tasks.py"


def test_tasks_module_imports_when_loaded_by_file_path():
    """Regression: `inspect eval constitutional_drift/tasks.py@constitution_edit`.

    Inspect loads a task file as a standalone module, not as a package member, so a
    relative import in tasks.py raises ModuleNotFoundError at CLI load time.
    """
    spec = importlib.util.spec_from_file_location("_standalone_tasks", TASKS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # must not raise
    assert hasattr(module, "constitution_edit")


def test_factor_specs_accept_the_list_the_cli_supplies():
    """Regression: Inspect splits `-T authority=a,b` into a list before the task sees it."""
    assert parse_values("authority", ["optional", "conservative"]) == [
        "optional",
        "conservative",
    ]
    assert parse_values("authority", "optional,conservative") == [
        "optional",
        "conservative",
    ]
    task = constitution_edit(authority=["optional", "conservative"])
    assert len(task.dataset) == 2


def test_default_task_is_a_single_reference_cell():
    task = constitution_edit()
    assert len(task.dataset) == 1
    assert task.dataset[0].id == Condition().id


def test_lists_expand_to_one_sample_per_cell_with_unique_ids():
    task = constitution_edit(authority="all", deliberation="none,explicit")
    assert len(task.dataset) == len(AUTHORITY) * 2
    assert len({s.id for s in task.dataset}) == len(task.dataset)


def test_sample_provisions_exactly_one_file_at_the_expected_path():
    sample = constitution_edit().dataset[0]
    assert list(sample.files) == [CONSTITUTION_PATH]
    assert Path(sample.files[CONSTITUTION_PATH]).is_file()


def test_sample_input_is_the_condition_prompt_and_metadata_pins_c0():
    condition = Condition(authority="edit_seeking", seed="c0_minimal")
    sample = constitution_edit(authority="edit_seeking", seed="c0_minimal").dataset[0]
    assert sample.input == build_prompt(condition)
    assert sample.metadata["condition"] == condition.as_dict()
    assert sample.metadata["c0_sha256"] == condition.seed_sha256()
    # The scorer diffs against this text, so it must be the exact provisioned bytes.
    assert sample.metadata["c0_text"] == Path(
        sample.files[CONSTITUTION_PATH]
    ).read_text(encoding="utf-8")


def test_seed_selects_the_file_without_changing_the_prompt():
    a = constitution_edit(seed="c0_broad_consensus").dataset[0]
    b = constitution_edit(seed="c0_minimal").dataset[0]
    assert a.input == b.input
    assert a.files[CONSTITUTION_PATH] != b.files[CONSTITUTION_PATH]
    assert a.metadata["c0_sha256"] != b.metadata["c0_sha256"]


def test_task_uses_a_docker_sandbox_with_the_repo_compose_file():
    task = constitution_edit()
    assert task.sandbox.type == "docker"
    assert task.sandbox.config == COMPOSE_FILE
    assert Path(COMPOSE_FILE).is_file()


def test_task_metadata_records_the_grid_that_was_requested():
    task = constitution_edit(authority="optional,neutral", identity="all")
    assert task.metadata["experiment"] == "1_constitution_edit"
    assert task.metadata["grid"]["authority"] == "optional,neutral"
    assert task.metadata["n_cells"] == len(task.dataset)


def test_limits_are_set_so_a_stuck_sample_is_scored_not_hung():
    task = constitution_edit(message_limit=12, time_limit=60)
    assert task.message_limit == 12
    assert task.time_limit == 60


def test_invalid_factor_value_fails_at_task_construction():
    with pytest.raises(ValueError, match="authority"):
        constitution_edit(authority="please_edit_a_lot")


# --- ablation-study arms: solver wiring without a model or Docker -------------------


def _run_solver_with_fakes(monkeypatch, condition):
    """Run constitution_editor() with a fake generate and a fake react agent.

    Returns (messages the agent received, state after the solver).
    """
    import asyncio

    from inspect_ai.model import ChatMessageAssistant, ChatMessageUser, ModelOutput
    from inspect_ai.solver import TaskState

    from constitutional_drift import tasks as tasks_mod
    from constitutional_drift.prompts import build_prompt

    seen: dict = {}

    def fake_react(**kwargs):
        seen["instructions"] = kwargs["prompt"].instructions
        return "agent"

    def fake_as_solver(agent):
        async def run(state, generate):
            seen["messages"] = list(state.messages)
            return state
        return run

    monkeypatch.setattr(tasks_mod, "react", fake_react)
    monkeypatch.setattr(tasks_mod, "as_solver", fake_as_solver)

    async def fake_generate(state, tool_calls="loop", **kwargs):
        seen["generate_tool_calls"] = tool_calls
        seen["generate_saw"] = list(state.messages)
        state.output = ModelOutput.from_content("mockllm/model", "MY BLIND VIEW")
        state.messages.append(ChatMessageAssistant(content="MY BLIND VIEW"))
        return state

    state = TaskState(
        model="mockllm/model", sample_id="s", epoch=1,
        input=build_prompt(condition),
        messages=[ChatMessageUser(content=build_prompt(condition))],
        metadata={"condition": condition.as_dict()},
    )
    solver = tasks_mod.constitution_editor()
    state = asyncio.run(solver(state, fake_generate))
    return seen, state


def test_blind_arm_sends_tool_free_view_turn_before_the_task(monkeypatch):
    from constitutional_drift.conditions import Condition
    from constitutional_drift.prompts import build_blind_prompt, build_prompt

    c = Condition(seed="c0_minimal", deliberation="blind")
    seen, state = _run_solver_with_fakes(monkeypatch, c)
    assert seen["generate_tool_calls"] == "none"
    # The blind turn saw only the blind prompt, never the task (which names the file).
    assert [m.text for m in seen["generate_saw"]] == [build_blind_prompt(c)]
    texts = [m.text for m in seen["messages"]]
    assert texts == [build_blind_prompt(c), "MY BLIND VIEW", build_prompt(c)]
    assert state.metadata["blind_draft"] == "MY BLIND VIEW"


def test_non_blind_arm_goes_straight_to_the_agent(monkeypatch):
    from constitutional_drift.conditions import Condition
    from constitutional_drift.prompts import build_prompt

    c = Condition(seed="c0_minimal")
    seen, _ = _run_solver_with_fakes(monkeypatch, c)
    assert "generate_saw" not in seen
    assert [m.text for m in seen["messages"]] == [build_prompt(c)]


def test_self_draft_sample_has_empty_workspace_but_governed_system_message():
    from constitutional_drift.conditions import Condition
    from constitutional_drift.prompts import build_system_message
    from constitutional_drift.tasks import _sample

    c = Condition(seed="c0_minimal", task="self_draft", embodiment="governed")
    sample = _sample(c)
    assert not sample.files
    system = build_system_message(c)
    assert system is not None and "Be helpful." in system
