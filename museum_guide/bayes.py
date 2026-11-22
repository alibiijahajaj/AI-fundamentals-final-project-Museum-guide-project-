"""Algorithm 2: Bayesian inference of the crowd state from noisy sensor readings."""

STATES = ("Crowded", "Quiet")
LEVELS = ("Low", "Medium", "High")
PRIOR = {"Crowded": 0.40, "Quiet": 0.60}
# P(reading | state) - hand-defined assumption (noisy people counter)
LIKELIHOOD = {
    "Crowded": {"Low": 0.10, "Medium": 0.30, "High": 0.60},
    "Quiet": {"Low": 0.60, "Medium": 0.30, "High": 0.10},
}


def update(belief, reading, likelihood=LIKELIHOOD):
    """One Bayes step: posterior(s) = P(reading|s) * belief(s) / P(reading)."""
    if reading not in LEVELS:
        raise ValueError(f"Unknown reading {reading!r}; expected one of {LEVELS}")
    unnorm = {s: likelihood[s][reading] * belief[s] for s in STATES}
    z = sum(unnorm.values())
    return {s: unnorm[s] / z for s in STATES}


def infer(readings, prior=PRIOR):
    """Apply several readings in sequence (assumed conditionally independent)."""
    belief = dict(prior)
    for r in readings:
        belief = update(belief, r)
    return belief
