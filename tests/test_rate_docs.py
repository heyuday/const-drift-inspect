"""The rater's prompt and axes must stay identical to the value-space analysis's."""

import ast
import importlib.util
from pathlib import Path

import pytest

# The value-space rater lives in the team repo: either this project is its inspect/
# directory, or the team repo is cloned next to this project as value-drift/.
_HERE = Path(__file__).resolve().parents[1]
REPO = next((p for p in (_HERE.parent, _HERE.parent / "value-drift")
             if (p / "constitutional_self_edit").is_dir()), _HERE.parent)
SELFHOST = REPO / "constitutional_self_edit" / "agents" / "scripts" / "selfhost_v3.py"
POSITION = REPO / "constitutional_self_edit" / "elicit" / "position.py"


def _load_rate_docs():
    spec = importlib.util.spec_from_file_location(
        "rate_docs", Path(__file__).resolve().parent.parent / "scripts" / "rate_docs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _constant(path: Path, name: str):
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return node.value
    raise KeyError(name)


@pytest.mark.skipif(not SELFHOST.exists(), reason="constitutional_self_edit not present")
def test_prompt_and_axes_match_the_value_space_rater():
    rd = _load_rate_docs()
    assert rd.RATE_PROMPT == ast.literal_eval(_constant(SELFHOST, "RATE_PROMPT"))
    assert rd.POSITION_AXES == ast.literal_eval(_constant(POSITION, "AXES"))
    extra = _constant(SELFHOST, "RATE_AXES")
    extra_keys = [ast.literal_eval(k) for k in extra.keys if k is not None]
    extra_vals = [ast.literal_eval(v) for k, v in zip(extra.keys, extra.values) if k is not None]
    assert {k: rd.RATE_AXES[k] for k in extra_keys} == dict(zip(extra_keys, extra_vals))
    assert list(rd.RATE_AXES) == list(rd.POSITION_AXES) + extra_keys


def test_parse_accepts_good_json_and_rejects_missing_axes():
    rd = _load_rate_docs()
    good = {k: 4 for k in rd.RATE_AXES}
    import json
    resp = {"choices": [{"message": {"content": json.dumps({"ratings": good, "summary": "x"})}}]}
    assert rd.parse(resp)[0] == good
    bad = dict(good)
    bad.pop("warmth")
    resp = {"choices": [{"message": {"content": json.dumps({"ratings": bad})}}]}
    with pytest.raises(ValueError):
        rd.parse(resp)
