#!/usr/bin/env python3
import sys, json

def is_grid_9x9(grid):
    if not isinstance(grid, list) or len(grid) != 9:
        return False
    for row in grid:
        if not isinstance(row, list) or len(row) != 9:
            return False
        for n in row:
            if not isinstance(n, int) or n < 0 or n > 9:
                return False
    return True

def check_contradictions(grid):
    # rows
    for r in range(9):
        seen = set()
        for c in range(9):
            v = grid[r][c]
            if v == 0: continue
            if v in seen:
                return f"Row {r+1} has duplicate {v}"
            seen.add(v)
    # cols
    for c in range(9):
        seen = set()
        for r in range(9):
            v = grid[r][c]
            if v == 0: continue
            if v in seen:
                return f"Column {c+1} has duplicate {v}"
            seen.add(v)
    # boxes
    for br in range(3):
        for bc in range(3):
            seen = set()
            for dr in range(3):
                for dc in range(3):
                    r = br*3+dr
                    c = bc*3+dc
                    v = grid[r][c]
                    if v == 0: continue
                    if v in seen:
                        return f"Box ({br+1},{bc+1}) has duplicate {v}"
                    seen.add(v)
    return None

def candidates(grid, r, c):
    if grid[r][c] != 0:
        return []
    present = set()
    for i in range(9):
        present.add(grid[r][i])
        present.add(grid[i][c])
    br = (r//3)*3
    bc = (c//3)*3
    for dr in range(3):
        for dc in range(3):
            present.add(grid[br+dr][bc+dc])
    return [d for d in range(1,10) if d not in present]

def find_hint(grid):
    # 1) Naked single
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                cand = candidates(grid, r, c)
                if len(cand) == 1:
                    return {
                        "type": "naked_single",
                        "message": f"Единственный кандидат {cand[0]} в клетке r{r+1}c{c+1}",
                        "placement": {"row": r, "col": c, "value": cand[0]},
                    }
    # 2) Hidden single in row
    for r in range(9):
        need = {d: [] for d in range(1,10)}
        for c in range(9):
            if grid[r][c] == 0:
                for d in candidates(grid, r, c):
                    need[d].append((r,c))
        for d in range(1,10):
            spots = need[d]
            if len(spots) == 1:
                rr, cc = spots[0]
                return {
                    "type": "hidden_single_row",
                    "message": f"Скрытый сингл {d} в строке {r+1} — позиция c{cc+1}",
                    "placement": {"row": rr, "col": cc, "value": d},
                }
    # 3) Hidden single in column
    for c in range(9):
        need = {d: [] for d in range(1,10)}
        for r in range(9):
            if grid[r][c] == 0:
                for d in candidates(grid, r, c):
                    need[d].append((r,c))
        for d in range(1,10):
            spots = need[d]
            if len(spots) == 1:
                rr, cc = spots[0]
                return {
                    "type": "hidden_single_col",
                    "message": f"Скрытый сингл {d} в столбце {c+1} — позиция r{rr+1}",
                    "placement": {"row": rr, "col": cc, "value": d},
                }
    # 4) Hidden single in box
    for br in range(3):
        for bc in range(3):
            need = {d: [] for d in range(1,10)}
            for dr in range(3):
                for dc in range(3):
                    r = br*3+dr
                    c = bc*3+dc
                    if grid[r][c] == 0:
                        for d in candidates(grid, r, c):
                            need[d].append((r,c))
            for d in range(1,10):
                spots = need[d]
                if len(spots) == 1:
                    rr, cc = spots[0]
                    return {
                        "type": "hidden_single_box",
                        "message": f"Скрытый сингл {d} в блоке ({br+1},{bc+1})",
                        "placement": {"row": rr, "col": cc, "value": d},
                    }
    return None

def gen_all_candidates(grid):
    return [[candidates(grid, r, c) for c in range(9)] for r in range(9)]

def locked_candidates(grid):
    # Pointing (box -> line) and Claiming (line -> box)
    cand = gen_all_candidates(grid)
    # Pointing: within each box, for each digit d, if all candidates lie in one row or one column
    for br in range(3):
        for bc in range(3):
            cells = [(br*3+dr, bc*3+dc) for dr in range(3) for dc in range(3)]
            for d in range(1,10):
                pos = [(r,c) for (r,c) in cells if d in cand[r][c]]
                if len(pos) <= 1:
                    continue
                rows = {r for r,_ in pos}
                cols = {c for _,c in pos}
                # All in one row -> eliminate d from that row outside box
                if len(rows) == 1:
                    r = next(iter(rows))
                    elim = []
                    cset = {c for _,c in pos}
                    for c in range(9):
                        if c in cset:
                            continue
                        if (c//3) == bc and (r//3) == br:
                            continue
                        if d in cand[r][c]:
                            elim.append({"row": r, "col": c, "remove": d})
                    if elim:
                        return {
                            "type": "locked_candidate_pointing",
                            "message": f"Pointing: цифра {d} в блоке ({br+1},{bc+1}) ограничена строкой {r+1}; удаляем {d} из остальных клеток строки",
                            "eliminations": elim,
                            "digit": d,
                            "box": {"br": br, "bc": bc}
                        }
                # All in one column -> eliminate d from that column outside box
                if len(cols) == 1:
                    c = next(iter(cols))
                    elim = []
                    rset = {r for r,_ in pos}
                    for r in range(9):
                        if r in rset:
                            continue
                        if (r//3) == br and (c//3) == bc:
                            continue
                        if d in cand[r][c]:
                            elim.append({"row": r, "col": c, "remove": d})
                    if elim:
                        return {
                            "type": "locked_candidate_pointing",
                            "message": f"Pointing: цифра {d} в блоке ({br+1},{bc+1}) ограничена столбцом {c+1}; удаляем {d} из остальных клеток столбца",
                            "eliminations": elim,
                            "digit": d,
                            "box": {"br": br, "bc": bc}
                        }
    # Claiming: row -> single box, column -> single box
    # Row-claiming
    for r in range(9):
        for d in range(1,10):
            cells = [(r,c) for c in range(9) if d in cand[r][c]]
            if len(cells) <= 1:
                continue
            boxes = {(r//3, c//3) for _, c in cells}
            if len(boxes) == 1:
                br, bc = boxes.pop()
                elim = []
                # remove d from other cells in that box not in row r
                for dr in range(3):
                    for dc in range(3):
                        rr = br*3+dr
                        cc = bc*3+dc
                        if rr == r:
                            continue
                        if d in cand[rr][cc]:
                            elim.append({"row": rr, "col": cc, "remove": d})
                if elim:
                    return {
                        "type": "locked_candidate_claiming",
                        "message": f"Claiming: в строке {r+1} все кандидаты {d} в блоке ({br+1},{bc+1}); удаляем {d} из других клеток блока",
                        "eliminations": elim,
                        "digit": d,
                        "box": {"br": br, "bc": bc}
                    }
    # Column-claiming
    for c in range(9):
        for d in range(1,10):
            cells = [(r,c) for r in range(9) if d in cand[r][c]]
            if len(cells) <= 1:
                continue
            boxes = {((r)//3, (c)//3) for r,_ in cells}
            if len(boxes) == 1:
                br, bc = boxes.pop()
                elim = []
                for dr in range(3):
                    for dc in range(3):
                        rr = br*3+dr
                        cc = bc*3+dc
                        if cc == c:
                            continue
                        if d in cand[rr][cc]:
                            elim.append({"row": rr, "col": cc, "remove": d})
                if elim:
                    return {
                        "type": "locked_candidate_claiming",
                        "message": f"Claiming: в столбце {c+1} все кандидаты {d} в блоке ({br+1},{bc+1}); удаляем {d} из других клеток блока",
                        "eliminations": elim,
                        "digit": d,
                        "box": {"br": br, "bc": bc}
                    }
    return None

def naked_pair(grid):
    cand = gen_all_candidates(grid)
    # helper across a unit: indices is list of (r,c)
    def check_unit(indices, unit_label):
        pairs = {}
        for (r,c) in indices:
            if grid[r][c] != 0:
                continue
            cs = cand[r][c]
            if len(cs) == 2:
                key = tuple(sorted(cs))
                pairs.setdefault(key, []).append((r,c))
        for key, cells in pairs.items():
            if len(cells) == 2:
                elim = []
                for (r,c) in indices:
                    if (r,c) in cells:
                        continue
                    if key[0] in cand[r][c] or key[1] in cand[r][c]:
                        for d in key:
                            if d in cand[r][c]:
                                elim.append({"row": r, "col": c, "remove": d})
                if elim:
                    return {
                        "type": "naked_pair",
                        "message": f"Голая пара {key} в {unit_label} — убираем кандидатов из остальных клеток юнита",
                        "eliminations": elim,
                        "pair": list(key)
                    }
        return None
    # rows
    for r in range(9):
        res = check_unit([(r,c) for c in range(9)], f"строке {r+1}")
        if res:
            return res
    # cols
    for c in range(9):
        res = check_unit([(r,c) for r in range(9)], f"столбце {c+1}")
        if res:
            return res
    # boxes
    for br in range(3):
        for bc in range(3):
            cells = [(br*3+dr, bc*3+dc) for dr in range(3) for dc in range(3)]
            res = check_unit(cells, f"блоке ({br+1},{bc+1})")
            if res:
                return res
    return None

def x_wing(grid):
    cand = gen_all_candidates(grid)
    # Row-based X-Wing: for each digit d, find two rows with the same two candidate columns
    for d in range(1,10):
        row_cols = []
        for r in range(9):
            cols = [c for c in range(9) if d in cand[r][c]]
            row_cols.append(cols)
        rows = [r for r in range(9) if len(row_cols[r]) == 2]
        for i in range(len(rows)):
            for j in range(i+1, len(rows)):
                r1, r2 = rows[i], rows[j]
                cset1 = set(row_cols[r1])
                cset2 = set(row_cols[r2])
                if cset1 == cset2 and len(cset1) == 2:
                    c1, c2 = sorted(list(cset1))
                    elim = []
                    for r in range(9):
                        if r in (r1, r2):
                            continue
                        for c in (c1, c2):
                            if d in cand[r][c]:
                                elim.append({"row": r, "col": c, "remove": d})
                    if elim:
                        return {
                            "type": "x_wing",
                            "message": f"X-Wing по строкам для цифры {d} на столбцах {c1+1},{c2+1}",
                            "eliminations": elim,
                            "digit": d,
                            "rows": [r1, r2],
                            "cols": [c1, c2]
                        }
    # Column-based X-Wing: symmetric
    for d in range(1,10):
        col_rows = []
        for c in range(9):
            rows = [r for r in range(9) if d in cand[r][c]]
            col_rows.append(rows)
        cols = [c for c in range(9) if len(col_rows[c]) == 2]
        for i in range(len(cols)):
            for j in range(i+1, len(cols)):
                c1, c2 = cols[i], cols[j]
                rset1 = set(col_rows[c1])
                rset2 = set(col_rows[c2])
                if rset1 == rset2 and len(rset1) == 2:
                    r1, r2 = sorted(list(rset1))
                    elim = []
                    for c in range(9):
                        if c in (c1, c2):
                            continue
                        for r in (r1, r2):
                            if d in cand[r][c]:
                                elim.append({"row": r, "col": c, "remove": d})
                    if elim:
                        return {
                            "type": "x_wing",
                            "message": f"X-Wing по столбцам для цифры {d} на строках {r1+1},{r2+1}",
                            "eliminations": elim,
                            "digit": d,
                            "rows": [r1, r2],
                            "cols": [c1, c2]
                        }
    return None

def find_advanced_hint(grid):
    # Try increasingly advanced patterns
    res = locked_candidates(grid)
    if res:
        return res
    res = naked_pair(grid)
    if res:
        return res
    res = x_wing(grid)
    if res:
        return res
    res = xy_wing(grid)
    if res:
        return res
    res = swordfish(grid)
    if res:
        return res
    return None

def main():
    raw = sys.stdin.read()
    try:
        req = json.loads(raw or "{}")
    except Exception:
        print(json.dumps({"ok": False, "error": "Invalid JSON input"}))
        return
    tool = req.get("tool")
    args = req.get("args") or {}
    if tool != "sudoku.hint":
        print(json.dumps({"ok": False, "error": "Unknown tool. Use sudoku.hint"}))
        return
    grid = args.get("grid")
    if not is_grid_9x9(grid):
        print(json.dumps({"ok": False, "error": "Grid must be 9x9 array of integers 0-9"}))
        return
    verbose = bool(args.get("verbose"))
    contradiction = check_contradictions(grid)
    if contradiction:
        print(json.dumps({"ok": False, "error": f"Contradiction: {contradiction}"}))
        return
    steps = []
    if verbose:
        steps.append("Проверка базовых синглов (naked, hidden)")
    hint = find_hint(grid)
    if not hint:
        if verbose:
            steps.append("Базовые не найдены; поиск продвинутых паттернов")
        adv = find_advanced_hint(grid)
        if not adv:
            res = {"type": "none", "message": "Подсказок не найдено на текущем уровне"}
            if verbose:
                res["steps"] = steps
            print(json.dumps({"ok": True, "result": res}, ensure_ascii=False))
            return
        if verbose:
            adv["steps"] = steps
        print(json.dumps({"ok": True, "result": adv}, ensure_ascii=False))
        return
    if verbose:
        hint["steps"] = steps
    print(json.dumps({"ok": True, "result": hint}, ensure_ascii=False))

# Helpers for advanced patterns
def peers_of(r, c):
    peers = set()
    for i in range(9):
        if i != c: peers.add((r, i))
        if i != r: peers.add((i, c))
    br = (r//3)*3
    bc = (c//3)*3
    for dr in range(3):
        for dc in range(3):
            rr = br+dr
            cc = bc+dc
            if rr == r and cc == c:
                continue
            peers.add((rr, cc))
    return peers

def xy_wing(grid):
    cand = gen_all_candidates(grid)
    # Find pivot with two candidates {x,y}
    for pr in range(9):
        for pc in range(9):
            if grid[pr][pc] != 0:
                continue
            pcands = cand[pr][pc]
            if len(pcands) != 2:
                continue
            x, y = pcands[0], pcands[1]
            pivot_peers = peers_of(pr, pc)
            # Collect pincers A with {x,z} and B with {y,z}
            As = []
            Bs = []
            for (ar, ac) in pivot_peers:
                if grid[ar][ac] != 0:
                    continue
                cands = cand[ar][ac]
                if len(cands) == 2:
                    if x in cands and y not in cands:
                        z = [d for d in cands if d != x][0]
                        As.append((ar, ac, z))
                    elif y in cands and x not in cands:
                        z = [d for d in cands if d != y][0]
                        Bs.append((ar, ac, z))
            # Pair A and B with same z
            for (ar, ac, z1) in As:
                for (br, bc, z2) in Bs:
                    if z1 != z2:
                        continue
                    z = z1
                    # Cells that see both A and B
                    inter = peers_of(ar, ac).intersection(peers_of(br, bc))
                    elim = []
                    for (rr, cc) in inter:
                        if (rr, cc) in [(pr, pc), (ar, ac), (br, bc)]:
                            continue
                        if grid[rr][cc] != 0:
                            continue
                        if z in cand[rr][cc]:
                            elim.append({"row": rr, "col": cc, "remove": z})
                    if elim:
                        return {
                            "type": "xy_wing",
                            "message": f"XY-Wing с опорой r{pr+1}c{pc+1}: пинцеры r{ar+1}c{ac+1} и r{br+1}c{bc+1} удаляют {z}",
                            "eliminations": elim,
                            "pivot": {"row": pr, "col": pc, "pair": [x,y]},
                            "pincers": [
                                {"row": ar, "col": ac, "pair": [x, z]},
                                {"row": br, "col": bc, "pair": [y, z]},
                            ],
                            "digit": z
                        }
    return None

def swordfish(grid):
    cand = gen_all_candidates(grid)
    # Row-based Swordfish
    for d in range(1,10):
        row_cols = [ [c for c in range(9) if d in cand[r][c]] for r in range(9) ]
        valid_rows = [r for r in range(9) if 2 <= len(row_cols[r]) <= 3]
        from itertools import combinations
        for r1, r2, r3 in combinations(valid_rows, 3):
            cols_union = set(row_cols[r1]) | set(row_cols[r2]) | set(row_cols[r3])
            if len(cols_union) != 3:
                continue
            if not set(row_cols[r1]).issubset(cols_union):
                continue
            if not set(row_cols[r2]).issubset(cols_union):
                continue
            if not set(row_cols[r3]).issubset(cols_union):
                continue
            elim = []
            cols_list = sorted(cols_union)
            for r in range(9):
                if r in (r1, r2, r3):
                    continue
                for c in cols_list:
                    if d in cand[r][c]:
                        elim.append({"row": r, "col": c, "remove": d})
            if elim:
                return {
                    "type": "swordfish",
                    "message": f"Swordfish по строкам для цифры {d} на строках {r1+1},{r2+1},{r3+1} и столбцах {cols_list[0]+1},{cols_list[1]+1},{cols_list[2]+1}",
                    "eliminations": elim,
                    "digit": d,
                    "rows": [r1, r2, r3],
                    "cols": cols_list
                }
    # Column-based Swordfish
    for d in range(1,10):
        col_rows = [ [r for r in range(9) if d in cand[r][c]] for c in range(9) ]
        valid_cols = [c for c in range(9) if 2 <= len(col_rows[c]) <= 3]
        from itertools import combinations
        for c1, c2, c3 in combinations(valid_cols, 3):
            rows_union = set(col_rows[c1]) | set(col_rows[c2]) | set(col_rows[c3])
            if len(rows_union) != 3:
                continue
            if not set(col_rows[c1]).issubset(rows_union):
                continue
            if not set(col_rows[c2]).issubset(rows_union):
                continue
            if not set(col_rows[c3]).issubset(rows_union):
                continue
            elim = []
            rows_list = sorted(rows_union)
            for c in range(9):
                if c in (c1, c2, c3):
                    continue
                for r in rows_list:
                    if d in cand[r][c]:
                        elim.append({"row": r, "col": c, "remove": d})
            if elim:
                return {
                    "type": "swordfish",
                    "message": f"Swordfish по столбцам для цифры {d} на столбцах {c1+1},{c2+1},{c3+1} и строках {rows_list[0]+1},{rows_list[1]+1},{rows_list[2]+1}",
                    "eliminations": elim,
                    "digit": d,
                    "rows": rows_list,
                    "cols": [c1, c2, c3]
                }
    return None

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
