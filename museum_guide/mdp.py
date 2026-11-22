"""Algorithm 3: MDP solved by value iteration; decision made under a Bayesian belief.

States : Crowded, Quiet          Actions: Visit Now, Visit Later
"Visit Now" ends the episode (terminal): the visitor enters and gets R_NOW[s].
"Visit Later" costs time (R_LATER) and the crowd may change (TRANS_LATER).
"""
from .bayes import STATES

ACTIONS = ("Visit Now", "Visit Later")
GAMMA = 0.9
R_NOW = {"Crowded": -2.0, "Quiet": 10.0}
R_LATER = {"Crowded": -1.0, "Quiet": -1.0}
TRANS_LATER = {
    "Crowded": {"Crowded": 0.5, "Quiet": 0.5},
    "Quiet": {"Crowded": 0.3, "Quiet": 0.7},
}


def value_iteration(gamma=GAMMA, eps=1e-10, max_iter=10_000):
    """Return (V, Q, iterations). Q[(s, a)] is the optimal action value."""
    V = {s: 0.0 for s in STATES}
    for i in range(1, max_iter + 1):
        Q = {}
        for s in STATES:
            Q[(s, "Visit Now")] = R_NOW[s]
            Q[(s, "Visit Later")] = R_LATER[s] + gamma * sum(
                TRANS_LATER[s][s2] * V[s2] for s2 in STATES
            )
        newV = {s: max(Q[(s, a)] for a in ACTIONS) for s in STATES}
        delta = max(abs(newV[s] - V[s]) for s in STATES)
        V = newV
        if delta < eps:
            break
    return V, Q, i


def decide(belief, Q):
    """Pick the action with the highest expected Q under the belief."""
    expected = {a: sum(belief[s] * Q[(s, a)] for s in STATES) for a in ACTIONS}
    return max(expected, key=expected.get), expected
