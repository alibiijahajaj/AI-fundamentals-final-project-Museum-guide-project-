"""Algorithm 1: A* search on a grid (4-direction moves, unit cost)."""
import heapq


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def neighbors(grid, cell):
    r, c = cell
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
            yield (nr, nc)


def astar(grid, start, goal):
    """Return (path, expanded_nodes); path is None if the goal is unreachable."""
    open_heap = [(manhattan(start, goal), 0, start)]  # (f, g, cell)
    came_from = {start: None}
    best_g = {start: 0}
    expanded = 0
    while open_heap:
        _, g, cur = heapq.heappop(open_heap)
        if g > best_g.get(cur, float("inf")):
            continue  # stale queue entry
        expanded += 1
        if cur == goal:
            path = []
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            return path[::-1], expanded
        for nxt in neighbors(grid, cur):
            ng = g + 1
            if ng < best_g.get(nxt, float("inf")):
                best_g[nxt] = ng
                came_from[nxt] = cur
                heapq.heappush(open_heap, (ng + manhattan(nxt, goal), ng, nxt))
    return None, expanded
