# 🏛️ Smart Museum Tour Guide

AI Fundamentals — Final Project. A tour planner that combines three AI topics in one pipeline:

| Step | Topic | Role |
|------|-------|------|
| 1 | **Bayesian inference** | Turns noisy people-counter readings into P(Crowded) for every exhibit |
| 2 | **MDP (value iteration)** | Turns that belief into *Visit Now* / *Visit Later* |
| 3 | **A\* search** | Routes the tour on an 8×8 map: "Now" exhibits first (nearest-first), "Later" exhibits after |

## Quick start (Python 3.9+, no external packages)

```bash
python app.py            # web UI at http://localhost:8000
python cli_demo.py       # console demo with 3 scenarios
python -m unittest discover -s tests -v    # 20 tests
```

## Project structure

```
app.py                   local web server + UI (standard library only)
cli_demo.py              console scenarios
museum_guide/
  astar.py               A* on a grid
  bayes.py               sequential Bayesian update
  mdp.py                 value iteration + belief-based decision
  planner.py             integration: Bayes -> MDP -> A*
tests/test_all.py        unit + API tests
docs/                    report, AI usage declaration, team statement, slides and defense plan
```

## Using the app
1. Pick one sensor reading (Low / Medium / High) per exhibit, or press a preset (*Quiet morning*, *Busy afternoon*, *Mixed day*).
2. Press **Plan my tour**. The page shows P(crowded) and the decision per exhibit, the tour order, and the coloured route on the map.

## Sample output (`python cli_demo.py`, "Mixed day")

```
A: P(crowded)=0.800 -> Visit Later
B: P(crowded)=0.100 -> Visit Now
C: P(crowded)=0.400 -> Visit Later
Leg 1: exhibit B (Visit Now), 10 steps
Leg 2: exhibit A (Visit Later), 3 steps
Leg 3: exhibit C (Visit Later), 14 steps
```

## Assumptions
All probabilities, rewards and transitions are hand-defined (see `bayes.py` and `mdp.py`); no real sensor data is used.

## License / AI usage
See `docs/AI_USAGE_DECLARATION.md`.
