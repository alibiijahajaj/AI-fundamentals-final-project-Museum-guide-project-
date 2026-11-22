"""Integration: Bayes -> MDP -> A*.

For every exhibit the sensor readings give a crowd belief (Bayes); the MDP turns the
belief into Visit Now / Visit Later; A* then routes the tour: "Now" exhibits first
(nearest-first), "Later" exhibits afterwards, giving crowds time to thin out.
"""
from .astar import astar
from .bayes import infer, PRIOR
from .mdp import value_iteration, decide

DEFAULT_MAP = [
    "S..#...A",
    ".#.#.#..",
    ".#...#B.",
    "...#....",
    "##.##.#.",
    "........",
    ".##.##..",
    "C....#..",
]


def find_cell(grid, ch):
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v == ch:
                return (r, c)


def exhibits(grid):
    return {
        ch: (r, c)
        for r, row in enumerate(grid)
        for c, ch in enumerate(row)
        if ch.isalpha() and ch != "S"
    }


def plan_tour(grid=DEFAULT_MAP, readings=None, prior=PRIOR):
    readings = readings or {}
    V, Q, iters = value_iteration()
    start = find_cell(grid, "S")
    ex = exhibits(grid)

    info = {}
    for name, pos in sorted(ex.items()):
        belief = infer(readings.get(name, []), prior)
        action, expected = decide(belief, Q)
        info[name] = {
            "position": pos,
            "readings": list(readings.get(name, [])),
            "belief": belief,
            "decision": action,
            "expected": expected,
        }

    legs, unreachable, cur = [], [], start
    for wanted in ("Visit Now", "Visit Later"):
        remaining = [n for n in info if info[n]["decision"] == wanted]
        while remaining:
            best = None
            for n in remaining:
                path, expanded = astar(grid, cur, ex[n])
                if path is None:
                    continue
                if best is None or len(path) < len(best[1]):
                    best = (n, path, expanded)
            if best is None:
                unreachable += remaining
                break
            n, path, expanded = best
            legs.append({"exhibit": n, "decision": wanted, "path": path,
                         "steps": len(path) - 1, "expanded": expanded})
            cur = ex[n]
            remaining.remove(n)

    return {
        "start": start,
        "exhibits": info,
        "tour": legs,
        "total_steps": sum(l["steps"] for l in legs),
        "unreachable": unreachable,
        "mdp": {
            "iterations": iters,
            "V": V,
            "Q": [{"state": s, "action": a, "q": q} for (s, a), q in Q.items()],
        },
    }
