"""Shortest-path solver and guaranteed-solvable random maze generator."""

from __future__ import annotations

from collections import deque
import csv
import random
from pathlib import Path
from typing import Iterable

Grid = list[list[str]]
KEYS = "abcdef"


def read_grid_csv(filename: str | Path) -> Grid:
    """Read a square maze CSV. Cells may be comma-separated or one row per line."""
    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        rows = [[cell.strip() for cell in row] for row in csv.reader(file) if row]
    if rows and len(rows) == 1 and len(rows[0]) > 1 and all(len(cell) == 1 for cell in rows[0]):
        # Also accept compact rows such as: S...#
        pass
    elif rows and all(len(row) == 1 for row in rows):
        rows = [list(row[0]) for row in rows]
    validate_grid(rows)
    return rows


def write_grid_csv(grid: Grid, filename: str | Path, path: Iterable[tuple[int, int]] = ()) -> None:
    """Write a comma-separated grid, annotating route cells without hiding symbols."""
    route = set(path)
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for r, row in enumerate(grid):
            writer.writerow([f"{cell}x" if (r, c) in route and cell not in "SE" else cell
                             for c, cell in enumerate(row)])


def validate_grid(grid: Grid) -> None:
    if not grid or any(len(row) != len(grid) for row in grid):
        raise ValueError("The maze must be a non-empty N x N grid.")
    allowed = set(".#SEabcdefABCDEF")
    if any(cell not in allowed for row in grid for cell in row):
        raise ValueError("Cells must be ., #, S, E, or letters a-f/A-F.")
    if sum(cell == "S" for row in grid for cell in row) != 1:
        raise ValueError("The maze must contain exactly one S.")
    if sum(cell == "E" for row in grid for cell in row) != 1:
        raise ValueError("The maze must contain exactly one E.")
    keys = {cell for row in grid for cell in row if cell in KEYS}
    doors = {cell.lower() for row in grid for cell in row if cell in "ABCDF"}
    if not doors <= keys:
        raise ValueError("Every door must have its matching key in the maze.")


def shortest_path(grid: Grid) -> list[tuple[int, int]] | None:
    """BFS over (row, column, key mask); returns route including S and E."""
    validate_grid(grid)
    n = len(grid)
    start = next((r, c) for r in range(n) for c in range(n) if grid[r][c] == "S")
    queue = deque([(start[0], start[1], 0)])
    previous: dict[tuple[int, int, int], tuple[int, int, int] | None] = {(start[0], start[1], 0): None}
    end_state = None
    while queue:
        r, c, mask = queue.popleft()
        if grid[r][c] == "E":
            end_state = (r, c, mask)
            break
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < n and 0 <= nc < n):
                continue
            cell = grid[nr][nc]
            if cell == "#":
                continue
            if cell in "ABCDF" and not (mask & (1 << (ord(cell.lower()) - ord("a")))):
                continue
            new_mask = mask
            if cell in KEYS:
                new_mask |= 1 << (ord(cell) - ord("a"))
            state = (nr, nc, new_mask)
            if state not in previous:
                previous[state] = (r, c, mask)
                queue.append(state)
    if end_state is None:
        return None
    route = []
    state = end_state
    while state is not None:
        route.append((state[0], state[1]))
        state = previous[state]
    return list(reversed(route))


def generate_maze(n: int, key_count: int, seed: int | None = None) -> Grid:
    """Generate a random N x N maze with T keys/doors and a guaranteed route."""
    if not 5 <= n <= 100:
        raise ValueError("Maze size must be between 5 and 100.")
    if not 1 <= key_count <= 5:
        raise ValueError("At most 5 unambiguous key/door pairs can be generated: E is reserved for the exit, so door E cannot be distinguished from it.")
    if n * n < 2 * key_count + 2:
        raise ValueError("Maze is too small for the requested keys and doors.")
    rng = random.Random(seed)
    # A random self-avoiding walk is the guaranteed route. Reserve separated
    # route cells for start, keys, doors, and exit, in that order.
    for _ in range(200):
        start = (rng.randrange(n), rng.randrange(n))
        walk = [start]
        seen = {start}
        target_len = min(n * n, 4 * key_count + 7)
        while len(walk) < target_len:
            r, c = walk[-1]
            options = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
            options = [(a, b) for a, b in options if 0 <= a < n and 0 <= b < n and (a, b) not in seen]
            if not options:
                break
            nxt = rng.choice(options)
            walk.append(nxt)
            seen.add(nxt)
        if len(walk) >= 2 * key_count + 2:
            break
    else:
        raise ValueError("Could not generate a route; try a larger maze.")
    grid = [["#" if rng.random() < 0.32 else "." for _ in range(n)] for _ in range(n)]
    for r, c in walk:
        grid[r][c] = "."
    grid[walk[0][0]][walk[0][1]] = "S"
    grid[walk[-1][0]][walk[-1][1]] = "E"
    # Place each key then its door along the walk; all other cells remain random.
    slots = list(range(1, len(walk) - 1))
    chosen = sorted(rng.sample(slots, 2 * key_count))
    # Pair consecutive selected cells so every key precedes its door.
    # E is reserved by the input format for the exit, so that door label
    # cannot be represented unambiguously. Use the other five door symbols.
    pair_letters = "abcdf"
    for i, letter in enumerate(pair_letters[:key_count]):
        for pos, symbol in ((chosen[2 * i], letter), (chosen[2 * i + 1], letter.upper())):
            r, c = walk[pos]
            grid[r][c] = symbol
    validate_grid(grid)
    return grid


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate or solve a keys-and-doors maze.")
    parser.add_argument("csv", nargs="?", help="Input CSV maze; omit to generate one")
    parser.add_argument("--size", type=int, default=15)
    parser.add_argument("--keys", type=int, default=3, help="Key/door pairs when generating")
    parser.add_argument("--output", default="maze_solution.csv")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    maze = read_grid_csv(args.csv) if args.csv else generate_maze(args.size, args.keys, args.seed)
    route = shortest_path(maze)
    print(len(route) - 1 if route else -1)
    if route:
        write_grid_csv(maze, args.output, route)
        print(f"Path-marked maze saved to {args.output}")
