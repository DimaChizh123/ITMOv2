#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def fail(msg):
    print(f"VERIFY FAIL: {msg}")
    sys.exit(1)

def ok(msg):
    print(f"VERIFY OK: {msg}")

def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    # Check AGENTS.md exists and mentions sudoku tool rule
    agents = (ROOT/"AGENTS.md")
    if not agents.exists():
        fail("AGENTS.md missing")
    txt = agents.read_text(encoding="utf-8")
    if "sudoku" not in txt or "sudoku.hint" not in txt:
        fail("AGENTS.md must instruct to use MCP sudoku.hint")

    # Check opencode config
    cfgp = ROOT/".opencode"/"opencode.json"
    if not cfgp.exists():
        fail(".opencode/opencode.json missing")
    cfg = read_json(cfgp)
    if "mcp" not in cfg or "sudoku" not in cfg["mcp"]:
        fail("MCP sudoku not configured")

    # Skill presence
    skill = ROOT/".opencode"/"skills"/"sudoku-assistant"/"SKILL.md"
    if not skill.exists():
        fail("sudoku-assistant skill missing")

    # MCP file exists
    mcp_entry = ROOT/"mcp"/"sudoku"/"index.py"
    if not mcp_entry.exists():
        fail("mcp/sudoku/index.py missing")

    ok("files present")

    # Quick runtime smoke: feed a simple grid with a naked single
    grid = [
        [0,0,0,2,6,0,7,0,1],
        [6,8,0,0,7,0,0,9,0],
        [1,9,0,0,0,4,5,0,0],
        [8,2,0,1,0,0,0,4,0],
        [0,0,4,6,0,2,9,0,0],
        [0,5,0,0,0,3,0,2,8],
        [0,0,9,3,0,0,0,7,4],
        [0,4,0,0,5,0,0,3,6],
        [7,0,3,0,1,8,0,0,0]
    ]
    import subprocess, os
    proc = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":grid}}).encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        fail(f"python exited {proc.returncode}: {proc.stderr.decode(errors='ignore')}")
    try:
        out = json.loads(proc.stdout.decode())
    except Exception as e:
        fail(f"invalid JSON from MCP: {e}\n{proc.stdout[:200]}...")
    if not out.get("ok"):
        fail(f"MCP returned error: {out}")
    if out.get("result",{}).get("type") not in (
        "naked_single",
        "hidden_single_row",
        "hidden_single_col",
        "hidden_single_box",
        "locked_candidate_pointing",
        "locked_candidate_claiming",
        "naked_pair",
        "x_wing",
        "xy_wing",
        "swordfish",
        "none",
    ):
        fail(f"unexpected hint type: {out}")
    # Verbose path check
    procv = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":grid, "verbose": True}}).encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    outv = json.loads(procv.stdout.decode())
    if outv.get("ok") and outv["result"]["type"] != "none":
        if "steps" not in outv["result"]:
            fail("verbose result must include steps")
    ok("MCP smoke passed")

    # Error case: wrong shape
    proc2 = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":[[1,2],[3,4]]}}).encode(), stdout=subprocess.PIPE)
    out2 = json.loads(proc2.stdout.decode())
    if out2.get("ok", True):
        fail("MCP should fail on invalid grid")
    ok("error path validated")

    # patterns: list non-empty and includes naked_single
    proc_list = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{}}).encode(), stdout=subprocess.PIPE)
    out_list = json.loads(proc_list.stdout.decode())
    if not out_list.get("ok"):
        fail(f"patterns list failed: {out_list}")
    patterns = out_list.get("result", {}).get("patterns", [])
    if not patterns:
        fail("patterns list is empty")
    if "naked_single" not in patterns:
        fail("patterns list must include naked_single")
    # strict synchronization: expected set equals support in hint (excluding none)
    expected = {
        "naked_single","hidden_single_row","hidden_single_col","hidden_single_box",
        "locked_candidate_pointing","locked_candidate_claiming","naked_pair","x_wing","xy_wing","swordfish"
    }
    if set(patterns) != expected:
        fail(f"patterns list mismatch: {patterns}")

    # pattern card x_wing required fields
    proc_card = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{"pattern":"x_wing"}}).encode(), stdout=subprocess.PIPE)
    out_card = json.loads(proc_card.stdout.decode())
    if not out_card.get("ok"):
        fail(f"x_wing card failed: {out_card}")
    card = out_card.get("result", {})
    for key in ("id","title","difficulty","summary","intuition","how_to_apply","example"):
        if key not in card:
            fail(f"x_wing card missing field: {key}")
    ex = card["example"]
    grid_ex = ex.get("grid")
    if not isinstance(grid_ex, list) or len(grid_ex) != 9 or any(not isinstance(r, list) or len(r) != 9 for r in grid_ex):
        fail("x_wing example.grid must be 9x9")
    hl = ex.get("highlights", {})
    if "cells" not in hl or "eliminations" not in hl:
        fail("x_wing example.highlights must have cells and eliminations")

    # unknown pattern error
    proc_unknown = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{"pattern":"no_such"}}).encode(), stdout=subprocess.PIPE)
    out_unknown = json.loads(proc_unknown.stdout.decode())
    if out_unknown.get("ok", True) or "Unknown pattern id" not in out_unknown.get("error",""):
        fail("unknown pattern must return Unknown pattern id error")

    # invalid pattern (not a non-empty string)
    proc_invalid_pat = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{"pattern":""}}).encode(), stdout=subprocess.PIPE)
    out_invalid_pat = json.loads(proc_invalid_pat.stdout.decode())
    if out_invalid_pat.get("ok", True) or "'pattern' must be a non-empty string" not in out_invalid_pat.get("error",""):
        fail("empty pattern must return non-empty string error")

    # extra args should be rejected
    proc_extra = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{"grid":[[]]}}).encode(), stdout=subprocess.PIPE)
    out_extra = json.loads(proc_extra.stdout.decode())
    if out_extra.get("ok", True) or "only 'pattern' is supported" not in out_extra.get("error",""):
        fail("extra args must be rejected")
    ok("patterns tests passed")

if __name__ == "__main__":
    main()
