"""Console demo: three scenarios, printing the Bayes / MDP / A* results."""
from museum_guide import plan_tour

SCENARIOS = {
    "Quiet day": {"A": ["Low"], "B": ["Low"], "C": ["Low"]},
    "Busy day": {"A": ["High"], "B": ["High"], "C": ["High"]},
    "Mixed day": {"A": ["High"], "B": ["Low"], "C": ["Medium"]},
}

for title, readings in SCENARIOS.items():
    plan = plan_tour(readings=readings)
    print("=" * 60)
    print(title, "| readings:", readings)
    for name, info in plan["exhibits"].items():
        print(f"  {name}: P(crowded)={info['belief']['Crowded']:.3f} -> {info['decision']}")
    for i, leg in enumerate(plan["tour"], 1):
        print(f"  Leg {i}: exhibit {leg['exhibit']} ({leg['decision']}), {leg['steps']} steps")
    print("  Total steps:", plan["total_steps"])
