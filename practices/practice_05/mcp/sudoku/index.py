#!/usr/bin/env python3
import sys, json
from typing import List, Dict, Any, Optional

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
    # Optional visual flags; default off to preserve backward compatibility
    visual = bool(args.get("visual", False))
    html_out = args.get("html_out")
    if html_out is not None and not isinstance(html_out, str):
        print(json.dumps({"ok": False, "error": "Invalid arguments: 'html_out' must be a string path"}))
        return

    # Static registry of pattern cards for sudoku.patterns
    PATTERN_CARDS = {
        "naked_single": {
            "id": "naked_single",
            "title": "Голый сингл (Naked Single)",
            "difficulty": "Базовый",
            "summary": "Клетка, у которой остаётся ровно один возможный кандидат.",
            "intuition": "Если все другие цифры исключены правилами строки/столбца/блока, остаётся единственный вариант.",
            "how_to_apply": [
                "Посчитайте кандидатов для пустых клеток.",
                "Найдите клетки с одним кандидатом.",
                "Поставьте это значение и обновите кандидатов."
            ],
            "example": {
                "grid": [[0,0,0,0,4,0,0,0,0],[0,0,0,0,7,0,0,0,0],[0,0,0,0,6,0,0,0,0],[0,0,0,0,2,0,0,0,0],[1,2,3,4,0,5,6,7,8],[0,0,0,0,1,0,0,0,0],[0,0,0,0,3,0,0,0,0],[0,0,0,0,5,0,0,0,0],[0,0,0,0,8,0,0,0,0]],
                "highlights": {
                    "cells": [{"row":4, "col":4}],
                    "eliminations": []
                }
            },
            "see_also": ["hidden_single_row","hidden_single_col","hidden_single_box"]
        },
        "hidden_single_row": {
            "id": "hidden_single_row",
            "title": "Скрытый сингл в строке (Hidden Single in Row)",
            "difficulty": "Базовый",
            "summary": "Единственный допустимый кандидат в строке для конкретной цифры.",
            "intuition": "Если цифра может стоять только в одной клетке строки, это скрытый сингл.",
            "how_to_apply": ["Определите кандидатов по строке.", "Найдите цифру с единственной позицией.", "Заполните клетку."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":0,"col":0}], "eliminations": []}}
        },
        "hidden_single_col": {
            "id": "hidden_single_col",
            "title": "Скрытый сингл в столбце (Hidden Single in Column)",
            "difficulty": "Базовый",
            "summary": "Единственный допустимый кандидат в столбце для конкретной цифры.",
            "intuition": "Если цифра возможна только в одной клетке столбца, это скрытый сингл.",
            "how_to_apply": ["Определите кандидатов по столбцу.", "Найдите цифру с единственной позицией.", "Заполните клетку."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":2,"col":0}], "eliminations": []}}
        },
        "hidden_single_box": {
            "id": "hidden_single_box",
            "title": "Скрытый сингл в блоке (Hidden Single in Box)",
            "difficulty": "Базовый",
            "summary": "Единственный допустимый кандидат в 3×3 блоке.",
            "intuition": "Если цифра возможна только в одной клетке блока, это скрытый сингл.",
            "how_to_apply": ["Определите кандидатов в блоке.", "Найдите цифру с единственной позицией.", "Заполните клетку."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":1,"col":0}], "eliminations": []}}
        },
        "locked_candidate_pointing": {
            "id": "locked_candidate_pointing",
            "title": "Запертые кандидаты (Pointing)",
            "difficulty": "Средний",
            "summary": "Кандидаты цифры в блоке ограничены одной строкой или столбцом, что позволяет устранить их вне блока.",
            "intuition": "Если все кандидаты цифры в блоке лежат в одной линии, она не может стоять вне блока на этой линии.",
            "how_to_apply": ["Найдите блок, где кандидаты цифры в одной строке/столбце.", "Уберите эту цифру из остальных клеток соответствующей строки/столбца вне блока.", "Обновите кандидатов."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":1,"col":3},{"row":1,"col":4},{"row":1,"col":5}], "eliminations": [{"row":1,"col":0,"digit":9},{"row":1,"col":2,"digit":9}]}}
        },
        "locked_candidate_claiming": {
            "id": "locked_candidate_claiming",
            "title": "Запертые кандидаты (Claiming)",
            "difficulty": "Средний",
            "summary": "Кандидаты цифры в строке/столбце ограничены одним блоком; можно удалить кандидатов в этом блоке в чужих строках/столбцах.",
            "intuition": "Если все кандидаты цифры строки/столбца лежат в одном блоке, то в других клетках блока эта цифра невозможна.",
            "how_to_apply": ["Найдите строку/столбец, где все кандидаты цифры в одном блоке.", "Уберите кандидатов из других клеток блока.", "Обновите кандидатов."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":4,"col":0},{"row":4,"col":1},{"row":4,"col":2}], "eliminations": [{"row":3,"col":1,"digit":4},{"row":5,"col":2,"digit":4}]}}
        },
        "naked_pair": {
            "id": "naked_pair",
            "title": "Голая пара (Naked Pair)",
            "difficulty": "Средний",
            "summary": "Две клетки в юните с одинаковыми двумя кандидатами позволяют убрать их из остальных клеток юнита.",
            "intuition": "Если пара {x,y} занимает две клетки, другие клетки юнита не могут содержать x или y.",
            "how_to_apply": ["Найдите две клетки с одинаковыми двумя кандидатами.", "Удалите эти кандидаты из остальных клеток юнита.", "Обновите кандидатов."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":0,"col":1},{"row":0,"col":2}], "eliminations": [{"row":0,"col":5,"digit":2},{"row":0,"col":6,"digit":7}]}}
        },
        "x_wing": {
            "id": "x_wing",
            "title": "Икс-крыло (X-Wing)",
            "difficulty": "Продвинутый",
            "summary": "Две строки и два столбца образуют прямоугольник для одной цифры; это позволяет удаления в других строках/столбцах.",
            "intuition": "Если кандидаты цифры в двух строках присутствуют ровно в двух одинаковых столбцах, образуется X-Wing.",
            "how_to_apply": ["Для выбранной цифры соберите кандидатов по строкам.", "Найдите две строки с одинаковыми двумя столбцами кандидатов.", "Удалите цифру из других строк в этих столбцах."],
            "example": {"grid": [[2,0,0,0,0,0,0,0,0],[0,0,5,0,0,0,0,0,0],[0,0,0,0,0,4,0,0,0],[0,0,0,1,0,0,0,4,0],[0,0,4,0,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":1,"col":1},{"row":1,"col":4},{"row":6,"col":1},{"row":6,"col":4}], "eliminations": [{"row":0,"col":1,"digit":5},{"row":3,"col":1,"digit":5},{"row":2,"col":4,"digit":5}]}}
        },
        "xy_wing": {
            "id": "xy_wing",
            "title": "XY-крыло (XY-Wing)",
            "difficulty": "Продвинутый",
            "summary": "Три клетки с парами {x,y}, {x,z}, {y,z} вокруг опоры позволяют удалить z из пересечений пинцеров.",
            "intuition": "Если пинцеры видят общие клетки, кандидат z удаляется из их пересечения.",
            "how_to_apply": ["Найдите опору с парой {x,y}.", "Найдите два пинцера с {x,z} и {y,z} среди её соседей.", "Удалите z из клеток, видимых обоими пинцерами."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":4,"col":4},{"row":4,"col":6},{"row":6,"col":4}], "eliminations": [{"row":6,"col":6,"digit":7},{"row":3,"col":4,"digit":7}]}}
        },
        "swordfish": {
            "id": "swordfish",
            "title": "Рыбий меч (Swordfish)",
            "difficulty": "Продвинутый",
            "summary": "Расширение X-Wing: три строки и три столбца формируют шаблон для удаления кандидатов.",
            "intuition": "Если для цифры кандидаты в трёх строках ограничены ровно тремя столбцами, возможны массовые удаления.",
            "how_to_apply": ["Для цифры соберите кандидатов по строкам.", "Найдите три строки с объединением из трёх столбцов.", "Удалите цифру из других строк в этих столбцах."],
            "example": {"grid": [[0,0,0,2,6,0,7,0,1],[6,8,0,0,7,0,0,9,0],[1,9,0,0,0,4,5,0,0],[8,2,0,1,0,0,0,4,0],[0,0,4,6,0,2,9,0,0],[0,5,0,0,0,3,0,2,8],[0,0,9,3,0,0,0,7,4],[0,4,0,0,5,0,0,3,6],[7,0,3,0,1,8,0,0,0]],
                        "highlights": {"cells": [{"row":0,"col":2},{"row":3,"col":2},{"row":5,"col":2},{"row":0,"col":4},{"row":3,"col":4},{"row":5,"col":4},{"row":0,"col":7},{"row":3,"col":7},{"row":5,"col":7}], "eliminations": [{"row":2,"col":2,"digit":3},{"row":7,"col":4,"digit":3}]}}
        },
    }

    if tool == "sudoku.patterns":
        # Strict arg validation: allow 'pattern' (required), optional 'visual' and 'html_out'
        if not args:
            # List mode
            patterns = list(PATTERN_CARDS.keys())
            print(json.dumps({"ok": True, "result": {"patterns": patterns}}, ensure_ascii=False))
            return
        allowed = {"pattern", "visual", "html_out"}
        if set(args.keys()) - allowed:
            print(json.dumps({"ok": False, "error": "Invalid arguments: only 'pattern', 'visual', and 'html_out' are supported"}))
            return
        pat = args.get("pattern")
        if not isinstance(pat, str) or len(pat.strip()) == 0:
            print(json.dumps({"ok": False, "error": "Invalid arguments: 'pattern' must be a non-empty string"}))
            return
        if pat not in PATTERN_CARDS:
            print(json.dumps({"ok": False, "error": f"Unknown pattern id: {pat}"}))
            return
        card = PATTERN_CARDS[pat]
        # Populate visual example if requested
        result_obj = card
        if visual:
            try:
                built_card = build_card(card, pat)
            except Exception as e:
                print(json.dumps({"ok": False, "error": f"Failed to build visual card: {str(e)}"}, ensure_ascii=False))
                return
            result_obj = built_card
            if html_out:
                html = render_html_for_patterns(result_obj)
                try:
                    with open(html_out, "w", encoding="utf-8") as f:
                        f.write(html)
                except Exception as e:
                    print(json.dumps({"ok": False, "error": f"Failed to write HTML: {str(e)}"}))
                    return
        print(json.dumps({"ok": True, "result": result_obj}, ensure_ascii=False))
        return

    if tool != "sudoku.hint":
        print(json.dumps({"ok": False, "error": "Unknown tool. Use sudoku.hint or sudoku.patterns"}))
        return

    # sudoku.hint path
    grid = args.get("grid")
    if not is_grid_9x9(grid):
        print(json.dumps({"ok": False, "error": "Grid must be 9x9 array of integers 0-9"}))
        return
    verbose = bool(args.get("verbose", True))
    contradiction = check_contradictions(grid)
    if contradiction:
        # Generate HTML on error if visual and html_out are provided
        if visual and html_out:
            try:
                cand = gen_all_candidates(grid)
                html = render_html_error(grid, cand, f"Contradiction: {contradiction}")
                with open(html_out, "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                print(json.dumps({"ok": False, "error": f"Failed to write HTML: {str(e)}"}))
                return
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
            # Attach visual grid/candidates if requested and HTML output if path provided
            if visual:
                res["visual"] = {
                    "grid": grid,
                    "candidates": gen_all_candidates(grid),
                    "pattern": None,
                    "action": None
                }
                if html_out:
                    try:
                        html = render_html_for_hint(res)
                        with open(html_out, "w", encoding="utf-8") as f:
                            f.write(html)
                    except Exception as e:
                        print(json.dumps({"ok": False, "error": f"Failed to write HTML: {str(e)}"}))
                        return
            print(json.dumps({"ok": True, "result": res}, ensure_ascii=False))
            return
        if verbose:
            adv["steps"] = steps
        # Visual/card/html attach if requested
        if visual:
            adv["visual"] = build_visual_block(adv, grid, PATTERN_CARDS)
            try:
                adv["card"] = build_card(PATTERN_CARDS.get(adv["type"], {}), adv["type"])
            except Exception:
                adv["card"] = None
            if html_out:
                try:
                    html = render_html_for_hint(adv)
                    with open(html_out, "w", encoding="utf-8") as f:
                        f.write(html)
                except Exception as e:
                    print(json.dumps({"ok": False, "error": f"Failed to write HTML: {str(e)}"}))
                    return
        print(json.dumps({"ok": True, "result": adv}, ensure_ascii=False))
        return
    if verbose:
        hint["steps"] = steps
    # Visual/card/html attach if requested
    if visual:
        hint["visual"] = build_visual_block(hint, grid, PATTERN_CARDS)
        try:
            hint["card"] = build_card(PATTERN_CARDS.get(hint["type"], {}), hint["type"])
        except Exception:
            hint["card"] = None
        if html_out:
            try:
                html = render_html_for_hint(hint)
                with open(html_out, "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                print(json.dumps({"ok": False, "error": f"Failed to write HTML: {str(e)}"}))
                return
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

# ===== Visual builders and HTML rendering =====

def build_visual_action(res: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Form {type, placement?, eliminations?} based on current fields.
    Uses 0-based coordinates and keys value/remove per contract.
    """
    placement = res.get("placement")
    eliminations = res.get("eliminations")
    if not placement and not eliminations:
        return None
    # If both present, prefer 'elimination' only when placement missing; otherwise 'placement'
    action_type = "placement" if placement else "elimination"
    action: Dict[str, Any] = {"type": action_type}
    if placement:
        action["placement"] = {"row": placement["row"], "col": placement["col"], "value": placement["value"]}
    if eliminations:
        action["eliminations"] = [{"row": e["row"], "col": e["col"], "remove": e["remove"]} for e in eliminations]
    return action

def build_visual_pattern(res: Dict[str, Any], grid: List[List[int]]) -> Optional[Dict[str, Any]]:
    """Build anchors with roles and params according to technique type.
    Minimal anchors are produced; roles map as per contract.
    """
    typ = res.get("type")
    if not typ or typ == "none":
        return None
    anchors: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {}
    cand = gen_all_candidates(grid)

    if typ in ("naked_single", "hidden_single_row", "hidden_single_col", "hidden_single_box"):
        pl = res.get("placement")
        if pl:
            anchors.append({"row": pl["row"], "col": pl["col"], "role": "target"})
    elif typ == "locked_candidate_pointing":
        d = res.get("digit")
        box = res.get("box") or {}
        br, bc = box.get("br"), box.get("bc")
        if d is not None and br is not None and bc is not None:
            for dr in range(3):
                for dc in range(3):
                    r = br*3+dr
                    c = bc*3+dc
                    if d in cand[r][c]:
                        anchors.append({"row": r, "col": c, "role": "box_candidate"})
            params = {"digit": d, "box": {"br": br, "bc": bc}}
    elif typ == "locked_candidate_claiming":
        d = res.get("digit")
        box = res.get("box") or {}
        br, bc = box.get("br"), box.get("bc")
        if d is not None and br is not None and bc is not None:
            # Try to find the constrained row in that box
            found_row = None
            for r in range(9):
                cells = [(r, c) for c in range(9) if d in cand[r][c]]
                boxes = {(r//3, c//3) for _, c in cells}
                if len(cells) >= 2 and boxes == {(br, bc)}:
                    found_row = r
                    break
            if found_row is not None:
                for c in range(9):
                    if d in cand[found_row][c] and (found_row//3, c//3) == (br, bc):
                        anchors.append({"row": found_row, "col": c, "role": "row_candidate"})
                params = {"digit": d, "box": {"br": br, "bc": bc}, "row": found_row}
            else:
                # else try column
                found_col = None
                for c in range(9):
                    cells = [(r, c) for r in range(9) if d in cand[r][c]]
                    boxes = {((r)//3, (c)//3) for r, _ in cells}
                    if len(cells) >= 2 and boxes == {(br, bc)}:
                        found_col = c
                        break
                if found_col is not None:
                    for r in range(9):
                        if d in cand[r][found_col] and (r//3, found_col//3) == (br, bc):
                            anchors.append({"row": r, "col": found_col, "role": "col_candidate"})
                    params = {"digit": d, "box": {"br": br, "bc": bc}, "col": found_col}
    elif typ == "naked_pair":
        pair = res.get("pair") or []
        elim = res.get("eliminations") or []
        unit = None
        if elim:
            rows = {e["row"] for e in elim}
            cols = {e["col"] for e in elim}
            if len(rows) == 1:
                unit = ("row", list(rows)[0])
            elif len(cols) == 1:
                unit = ("col", list(cols)[0])
            else:
                boxes = {((e["row"]//3), (e["col"]//3)) for e in elim}
                if len(boxes) == 1:
                    unit = ("box", list(boxes)[0])
        if unit:
            kind, idx = unit
            indices = []
            if kind == "row":
                indices = [(idx, c) for c in range(9)]
            elif kind == "col":
                indices = [(r, idx) for r in range(9)]
            elif kind == "box":
                br, bc = idx
                indices = [(br*3+dr, bc*3+dc) for dr in range(3) for dc in range(3)]
            for (r, c) in indices:
                cs = cand[r][c]
                if len(cs) == 2 and sorted(cs) == sorted(pair):
                    anchors.append({"row": r, "col": c, "role": "pair"})
            params = {"pair": pair, "unit": unit}
    elif typ == "x_wing":
        d = res.get("digit")
        rows = res.get("rows") or []
        cols = res.get("cols") or []
        for r in rows:
            for c in cols:
                anchors.append({"row": r, "col": c, "role": "corner"})
        params = {"digit": d, "rows": rows, "cols": cols}
    elif typ == "xy_wing":
        pivot = res.get("pivot")
        pincers = res.get("pincers") or []
        if pivot:
            anchors.append({"row": pivot["row"], "col": pivot["col"], "role": "pivot"})
        for p in pincers:
            anchors.append({"row": p["row"], "col": p["col"], "role": "pincer"})
        params = {"pivot": pivot, "pincers": pincers}
    elif typ == "swordfish":
        d = res.get("digit")
        rows = res.get("rows") or []
        cols = res.get("cols") or []
        for r in rows:
            for c in cols:
                if d is None or d in cand[r][c]:
                    anchors.append({"row": r, "col": c, "role": "corner"})
        params = {"digit": d, "rows": rows, "cols": cols}
    else:
        return None
    return {"id": typ, "anchors": anchors, "params": params or None}

def build_visual_block(res: Dict[str, Any], grid: List[List[int]], cards: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "grid": grid,
        "candidates": gen_all_candidates(grid),
        "pattern": build_visual_pattern(res, grid),
        "action": build_visual_action(res)
    }

def build_card(card_src: Dict[str, Any], type_id: str) -> Dict[str, Any]:
    example = card_src.get("example") or {}
    ex_grid = example.get("grid")
    if not is_grid_9x9(ex_grid):
        return {k: card_src[k] for k in ("id","title","difficulty","summary","intuition","how_to_apply") if k in card_src}
    ex_cand = gen_all_candidates(ex_grid)
    hl = example.get("highlights") or {"cells": [], "eliminations": []}
    cells = hl.get("cells") or []
    elims = hl.get("eliminations") or []
    anchors: List[Dict[str, Any]] = []
    if type_id in ("naked_single", "hidden_single_row", "hidden_single_col", "hidden_single_box"):
        if cells:
            anchors.append({"row": cells[0]["row"], "col": cells[0]["col"], "role": "target"})
    elif type_id == "locked_candidate_pointing":
        for cell in cells:
            anchors.append({"row": cell["row"], "col": cell["col"], "role": "box_candidate"})
    elif type_id == "locked_candidate_claiming":
        for cell in cells:
            anchors.append({"row": cell["row"], "col": cell["col"], "role": "row_candidate"})
    elif type_id == "naked_pair":
        for cell in cells:
            anchors.append({"row": cell["row"], "col": cell["col"], "role": "pair"})
    elif type_id == "x_wing":
        for cell in cells:
            anchors.append({"row": cell["row"], "col": cell["col"], "role": "corner"})
    elif type_id == "xy_wing":
        for i, cell in enumerate(cells):
            anchors.append({"row": cell["row"], "col": cell["col"], "role": "pivot" if i == 0 else "pincer"})
    elif type_id == "swordfish":
        for cell in cells:
            anchors.append({"row": cell["row"], "col": cell["col"], "role": "corner"})
    action: Optional[Dict[str, Any]] = None
    elim_list = [{"row": e["row"], "col": e["col"], "remove": e.get("digit")} for e in elims if e.get("digit")]
    if elim_list:
        action = {"type": "elimination", "eliminations": elim_list}
    else:
        if anchors:
            r, c = anchors[0]["row"], anchors[0]["col"]
            cs = ex_cand[r][c]
            if len(cs) == 1:
                action = {"type": "placement", "placement": {"row": r, "col": c, "value": cs[0]}}
    out = {k: card_src[k] for k in ("id","title","difficulty","summary","intuition","how_to_apply") if k in card_src}
    out["example"] = {
        "grid": ex_grid,
        "candidates": ex_cand,
        "pattern": {"id": type_id, "anchors": anchors, "params": None},
        "action": action
    }
    return out

def render_html_for_hint(res: Dict[str, Any]) -> str:
    result = res if res.get("type") else res.get("result", {})
    visual = result.get("visual") or {}
    card = result.get("card")
    title = f"Sudoku Hint: {result.get('type','none')}"
    return _render_html_page(title, visual, card, error=None)

def render_html_error(grid: List[List[int]], cand: List[List[List[int]]], error_msg: str) -> str:
    visual = {"grid": grid, "candidates": cand, "pattern": None, "action": None}
    return _render_html_page("Sudoku Error", visual, None, error=error_msg)

def render_html_for_patterns(card: Dict[str, Any]) -> str:
    title = f"Sudoku Pattern: {card.get('title','')}"
    visual = None
    return _render_html_page(title, visual, card, error=None)

def _render_html_page(title: str, visual: Optional[Dict[str, Any]], card: Optional[Dict[str, Any]], error: Optional[str]) -> str:
    css = """
    body { font-family: system-ui, sans-serif; margin: 0; padding: 16px; }
    .layout { display: grid; grid-template-columns: 1fr; gap: 16px; }
    @media (min-width: 640px) { .layout { grid-template-columns: 1fr 340px; } }
    .banner { padding: 12px; border-radius: 6px; margin-bottom: 12px; }
    .banner.error { background: #ffe5e5; color: #900; border: 1px solid #f99; }
    .header { margin-bottom: 8px; }
    .grid-wrap { display: grid; grid-template-columns: 24px auto; grid-template-rows: 24px auto; }
    .col-labels { display: grid; grid-template-columns: repeat(9, 1fr); }
    .row-labels { display: grid; grid-template-rows: repeat(9, 1fr); }
    .label { font-size: 12px; text-align: center; color: #555; }
    .board { display: grid; grid-template-columns: repeat(9, 1fr); grid-template-rows: repeat(9, 1fr); border: 2px solid #333; }
    .cell { aspect-ratio: 1 / 1; border: 1px solid #bbb; position: relative; display: flex; align-items: center; justify-content: center; }
    .cell.thick-right { border-right: 2px solid #333; }
    .cell.thick-bottom { border-bottom: 2px solid #333; }
    .digit { font-size: 22px; font-weight: 700; color: #111; }
    .pencil { position: absolute; inset: 4px; display: grid; grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(3, 1fr); font-size: 10px; color: #444; }
    .pencil .mark { display: grid; place-items: center; line-height: 1; height: 100%; width: 100%; }
    .anchor.primary { outline: 2px solid #2b6cb0; background: rgba(66, 153, 225, 0.15); }
    .anchor.secondary { outline: 2px solid #d69e2e; background: rgba(214, 158, 46, 0.15); }
    .placement { box-shadow: 0 0 0 3px #2f855a inset; background: rgba(72, 187, 120, 0.18); }
    .badge { position: absolute; top: 2px; right: 2px; background: #e53e3e; color: white; font-size: 9px; border-radius: 8px; padding: 0 4px; text-decoration: line-through; }
    .sidebar { border: 1px solid #ddd; border-radius: 6px; padding: 12px; }
    .sidebar h2 { margin: 0 0 8px 0; font-size: 16px; }
    .chips { color: #555; font-size: 12px; }
    ul { margin: 6px 0; }
    """
    def label_for_row(r):
        return f"r{r+1}"
    def label_for_col(c):
        return f"c{c+1}"
    def role_to_class(role: str) -> str:
        if role in ("pivot","target","pair","corner","box_candidate","line_candidate","row_candidate","col_candidate"):
            return "primary"
        if role == "pincer":
            return "secondary"
        return "primary"
    def render_board(v: Dict[str, Any]) -> str:
        grid = v.get("grid")
        cands = v.get("candidates") or [[[] for _ in range(9)] for _ in range(9)]
        anchors = (v.get("pattern") or {}).get("anchors") or []
        action = v.get("action") or {}
        placement = (action.get("placement") if action.get("type") == "placement" else None)
        elims = action.get("eliminations") or []
        anch_map: Dict[tuple, str] = {}
        for a in anchors:
            anch_map[(a["row"], a["col"])] = role_to_class(a.get("role"))
        elim_map: Dict[tuple, List[int]] = {}
        for e in elims:
            elim_map.setdefault((e["row"], e["col"]), []).append(e["remove"])
        html_cells = []
        for r in range(9):
            for c in range(9):
                classes = ["cell"]
                if c in (2,5): classes.append("thick-right")
                if r in (2,5): classes.append("thick-bottom")
                if (r,c) in anch_map:
                    classes.append(f"anchor {anch_map[(r,c)]}")
                if placement and placement.get("row") == r and placement.get("col") == c:
                    classes.append("placement")
                cell_html = f"<div class='{' '.join(classes)}' title='{label_for_row(r)}{label_for_col(c)}'>"
                val = grid[r][c]
                if isinstance(val, int) and val != 0:
                    cell_html += f"<div class='digit'>{val}</div>"
                else:
                    cell_html += "<div class='pencil'>"
                    for d in range(1,10):
                        mark = "" if d not in cands[r][c] else str(d)
                        badge = ""
                        # elimination badge even if mark absent
                        if (r,c) in elim_map and d in elim_map[(r,c)]:
                            badge = f"<span class='badge'>{d}</span>"
                        cell_html += f"<div class='mark'>{mark}{badge}</div>"
                    cell_html += "</div>"
                cell_html += "</div>"
                html_cells.append(cell_html)
        col_labels = "".join([f"<div class='label'>{label_for_col(c)}</div>" for c in range(9)])
        row_labels = "".join([f"<div class='label'>{label_for_row(r)}</div>" for r in range(9)])
        board = "".join(html_cells)
        return f"<div class='grid-wrap'><div></div><div class='col-labels'>{col_labels}</div><div class='row-labels'>{row_labels}</div><div class='board'>{board}</div></div>"
    parts = ["<html><head><meta charset='utf-8'><title>"+title+"</title><style>"+css+"</style></head><body>"]
    parts.append(f"<div class='header'><h1>{title}</h1></div>")
    if error:
        parts.append(f"<div class='banner error'>Error: {error}</div>")
    parts.append("<div class='layout'>")
    if visual:
        parts.append("<div>")
        parts.append(render_board(visual))
        parts.append("</div>")
    parts.append("<div class='sidebar'>")
    if card:
        parts.append(f"<h2>{card.get('title','—')}</h2>")
        parts.append(f"<div class='chips'>Сложность: {card.get('difficulty','—')}</div>")
        parts.append(f"<p>{card.get('summary','—')}</p>")
        parts.append(f"<p>{card.get('intuition','—')}</p>")
        hta = card.get('how_to_apply')
        if isinstance(hta, list):
            parts.append("<ul>" + "".join([f"<li>{x}</li>" for x in hta]) + "</ul>")
        elif isinstance(hta, str):
            parts.append("<ul><li>"+hta+"</li></ul>")
        ex = card.get('example')
        if ex and isinstance(ex, dict):
            parts.append("<h3>Наглядный пример</h3>")
            parts.append(render_board(ex))
    else:
        parts.append("<h2>Справка</h2><p>—</p>")
    parts.append("</div>")
    parts.append("</div>")
    parts.append("</body></html>")
    return "".join(parts)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
