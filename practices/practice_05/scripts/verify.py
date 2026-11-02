#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT/"test-results"

def fail(msg):
    print(f"VERIFY FAIL: {msg}")
    sys.exit(1)

def ok(msg):
    print(f"VERIFY OK: {msg}")

def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def main():
    # Ensure artifacts directory exists for generated outputs
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
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

    # extra args should be rejected (only pattern/visual/html_out allowed)
    proc_extra = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{"grid":[[]]}}).encode(), stdout=subprocess.PIPE)
    out_extra = json.loads(proc_extra.stdout.decode())
    if out_extra.get("ok", True) or "only 'pattern', 'visual', and 'html_out'" not in out_extra.get("error",""):
        fail("extra args must be rejected per new allowed set")
    ok("patterns tests passed")

    # Visual hint JSON mode: should include visual grid/candidates/action
    proc_vis = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":grid, "visual": True, "verbose": True}}).encode(), stdout=subprocess.PIPE)
    out_vis = json.loads(proc_vis.stdout.decode())
    if not out_vis.get("ok"):
        fail(f"visual hint failed: {out_vis}")
    res_vis = out_vis.get("result", {})
    visual = res_vis.get("visual")
    if not visual:
        fail("visual block missing in visual mode")
    vg = visual.get("grid")
    vc = visual.get("candidates")
    if not isinstance(vg, list) or len(vg) != 9 or any(len(r)!=9 for r in vg):
        fail("visual.grid must be 9x9")
    if not isinstance(vc, list) or len(vc) != 9 or any(len(r)!=9 for r in vc):
        fail("visual.candidates must be 9x9")
    action = visual.get("action")
    if action:
        t = action.get("type")
        if t == "placement":
            if "placement" not in action or "value" not in action["placement"]:
                fail("placement must have value")
        elif t == "elimination":
            el = action.get("eliminations") or []
            if not el or any("remove" not in e for e in el):
                fail("eliminations must include remove")
    ok("visual hint JSON validated")

    # HTML generation for hint
    hint_html = str(ARTIFACTS_DIR/"tmp-hint.html")
    proc_html = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":grid, "visual": True, "html_out": hint_html}}).encode(), stdout=subprocess.PIPE)
    out_html = json.loads(proc_html.stdout.decode())
    if not out_html.get("ok"):
        fail(f"hint with html_out failed: {out_html}")
    if not Path(hint_html).exists():
        fail("html_out file not created for hint")
    if "<html" not in Path(hint_html).read_text(encoding="utf-8"):
        fail("html_out content invalid (no <html)")
    ok("hint HTML generated")

    # None state visual + HTML
    empty_grid = [[0]*9 for _ in range(9)]
    none_html = str(ARTIFACTS_DIR/"tmp-none.html")
    proc_none = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":empty_grid, "visual": True, "html_out": none_html}}).encode(), stdout=subprocess.PIPE)
    out_none = json.loads(proc_none.stdout.decode())
    if not out_none.get("ok") or out_none["result"].get("type") != "none":
        fail("none visual expected")
    if not Path(none_html).exists():
        fail("none html_out file not created")
    ok("none visual HTML generated")

    # Contradiction visual + html_out must write HTML and return error
    bad_grid = [row[:] for row in grid]
    bad_grid[0][0] = 7
    bad_grid[2][0] = 7  # duplicate in column 1
    err_html = str(ARTIFACTS_DIR/"tmp-error.html")
    proc_err = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.hint","args":{"grid":bad_grid, "visual": True, "html_out": err_html}}).encode(), stdout=subprocess.PIPE)
    out_err = json.loads(proc_err.stdout.decode())
    if out_err.get("ok", True):
        fail("contradiction should return ok:false")
    if not Path(err_html).exists():
        fail("error html_out not written")
    ok("error visual HTML generated")

    # Patterns HTML generation with visual example
    pat_html = str(ARTIFACTS_DIR/"tmp-pattern.html")
    proc_pat = subprocess.run(["python3", str(mcp_entry)], input=json.dumps({"tool":"sudoku.patterns","args":{"pattern":"x_wing", "visual": True, "html_out": pat_html}}).encode(), stdout=subprocess.PIPE)
    out_pat = json.loads(proc_pat.stdout.decode())
    if not out_pat.get("ok"):
        fail(f"patterns visual failed: {out_pat}")
    if not Path(pat_html).exists():
        fail("patterns html_out not created")
    ok("patterns visual HTML generated")

if __name__ == "__main__":
    main()
