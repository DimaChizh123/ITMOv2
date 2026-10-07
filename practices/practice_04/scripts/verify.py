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
        fail("mcp/sudoku/index.js missing")

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
        fail(f"node exited {proc.returncode}: {proc.stderr.decode(errors='ignore')}")
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

if __name__ == "__main__":
    main()
