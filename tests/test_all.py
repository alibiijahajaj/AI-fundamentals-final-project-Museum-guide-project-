import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from museum_guide import DEFAULT_MAP, astar, infer, update, plan_tour, value_iteration, decide, PRIOR
from museum_guide.astar import neighbors
from museum_guide.planner import find_cell, exhibits


def bfs_len(grid, s, g):
    q, seen = deque([(s, 0)]), {s}
    while q:
        cur, d = q.popleft()
        if cur == g:
            return d
        for n in neighbors(grid, cur):
            if n not in seen:
                seen.add(n)
                q.append((n, d + 1))
    return None


class TestAStar(unittest.TestCase):
    def test_optimal_vs_bfs_for_all_exhibits(self):
        s = find_cell(DEFAULT_MAP, "S")
        for name, pos in exhibits(DEFAULT_MAP).items():
            path, _ = astar(DEFAULT_MAP, s, pos)
            self.assertEqual(len(path) - 1, bfs_len(DEFAULT_MAP, s, pos), name)

    def test_path_is_valid(self):
        s, g = find_cell(DEFAULT_MAP, "S"), find_cell(DEFAULT_MAP, "C")
        path, _ = astar(DEFAULT_MAP, s, g)
        self.assertEqual((path[0], path[-1]), (s, g))
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)
            self.assertNotEqual(DEFAULT_MAP[b[0]][b[1]], "#")

    def test_start_equals_goal(self):
        path, _ = astar(DEFAULT_MAP, (0, 0), (0, 0))
        self.assertEqual(path, [(0, 0)])

    def test_unreachable(self):
        grid = ["S#A"]
        self.assertIsNone(astar(grid, (0, 0), (0, 2))[0])


class TestBayes(unittest.TestCase):
    def test_single_high_reading(self):
        self.assertAlmostEqual(infer(["High"])["Crowded"], 0.8)

    def test_no_reading_returns_prior(self):
        self.assertEqual(infer([]), PRIOR)

    def test_normalized_and_order_independent(self):
        a, b = infer(["High", "Low", "Medium"]), infer(["Medium", "High", "Low"])
        self.assertAlmostEqual(sum(a.values()), 1.0)
        for s in a:
            self.assertAlmostEqual(a[s], b[s])

    def test_direction(self):
        self.assertGreater(infer(["High"])["Crowded"], PRIOR["Crowded"])
        self.assertLess(infer(["Low"])["Crowded"], PRIOR["Crowded"])
        self.assertGreater(infer(["High", "High"])["Crowded"], infer(["High"])["Crowded"])

    def test_invalid_reading(self):
        with self.assertRaises(ValueError):
            update(PRIOR, "Huge")


class TestMDP(unittest.TestCase):
    def test_converges_and_satisfies_bellman(self):
        V, Q, iters = value_iteration()
        self.assertLess(iters, 10_000)
        for s in V:
            self.assertAlmostEqual(V[s], max(Q[(s, "Visit Now")], Q[(s, "Visit Later")]), places=6)

    def test_known_values(self):
        V, Q, _ = value_iteration()
        self.assertAlmostEqual(Q[("Quiet", "Visit Now")], 10.0)
        self.assertAlmostEqual(V["Crowded"], 3.5 / 0.55, places=6)  # closed form

    def test_decision_threshold(self):
        _, Q, _ = value_iteration()
        self.assertEqual(decide({"Crowded": 0.05, "Quiet": 0.95}, Q)[0], "Visit Now")
        self.assertEqual(decide({"Crowded": 0.90, "Quiet": 0.10}, Q)[0], "Visit Later")

    def test_decision_monotonic_in_belief(self):
        _, Q, _ = value_iteration()
        flips = 0
        prev = decide({"Crowded": 0.0, "Quiet": 1.0}, Q)[0]
        for i in range(1, 101):
            p = i / 100
            cur = decide({"Crowded": p, "Quiet": 1 - p}, Q)[0]
            flips += cur != prev
            prev = cur
        self.assertEqual(flips, 1)


class TestPlanner(unittest.TestCase):
    def test_all_exhibits_visited_and_legs_connected(self):
        plan = plan_tour(readings={"A": ["High"], "B": ["Low"], "C": ["Medium"]})
        self.assertEqual({l["exhibit"] for l in plan["tour"]}, set("ABC"))
        cur = plan["start"]
        for leg in plan["tour"]:
            self.assertEqual(tuple(leg["path"][0]), tuple(cur))
            cur = leg["path"][-1]

    def test_now_before_later(self):
        plan = plan_tour(readings={"A": ["High", "High"], "B": ["Low"], "C": ["High"]})
        decisions = [l["decision"] for l in plan["tour"]]
        self.assertEqual(decisions, sorted(decisions, key=lambda d: d != "Visit Now"))
        self.assertEqual(plan["tour"][0]["exhibit"], "B")

    def test_quiet_day_everything_now(self):
        plan = plan_tour(readings={n: ["Low"] for n in "ABC"})
        self.assertTrue(all(l["decision"] == "Visit Now" for l in plan["tour"]))

    def test_total_steps(self):
        plan = plan_tour()
        self.assertEqual(plan["total_steps"], sum(l["steps"] for l in plan["tour"]))


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        cls.srv = app.make_server(0)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def _post(self, body):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/plan",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(req)

    def test_home_and_config(self):
        html = urllib.request.urlopen(f"http://127.0.0.1:{self.port}/").read().decode()
        self.assertIn("Smart Museum Tour Guide", html)
        cfg = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/config"))
        self.assertEqual(cfg["exhibit_names"], ["A", "B", "C"])

    def test_plan_ok(self):
        data = json.load(self._post({"readings": {"A": ["High"], "B": ["Low"]}}))
        self.assertEqual(len(data["tour"]), 3)

    def test_bad_input_gives_400(self):
        for bad in ({"readings": {"A": ["Huge"]}}, {"readings": {"Z": ["Low"]}}, {"readings": []}):
            with self.assertRaises(urllib.error.HTTPError) as cm:
                self._post(bad)
            self.assertEqual(cm.exception.code, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
