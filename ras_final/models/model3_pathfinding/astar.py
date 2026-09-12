"""A* pathfinding over a hazard-aware cost grid."""
from __future__ import annotations

import heapq
import math
from typing import Iterable, Sequence

Grid = Sequence[Sequence[float]]
Cell = tuple[int, int]


def find_path(cost_grid: Grid, start: Cell, goal: Cell, *, obstacle_cost: float = math.inf) -> list[Cell]:
    """Return the lowest-cost 4-connected path, including start and goal."""
    if not cost_grid or not cost_grid[0]:
        raise ValueError("cost_grid must contain at least one cell")
    width = len(cost_grid[0])
    if any(len(row) != width for row in cost_grid):
        raise ValueError("cost_grid must be rectangular")
    height = len(cost_grid)
    for cell in (start, goal):
        if not (0 <= cell[0] < height and 0 <= cell[1] < width):
            raise ValueError(f"cell {cell} is outside the grid")
        if float(cost_grid[cell[0]][cell[1]]) >= obstacle_cost:
            return []
    if start == goal:
        return [start]

    def heuristic(cell: Cell) -> float:
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

    frontier: list[tuple[float, int, Cell]] = [(heuristic(start), 0, start)]
    came_from: dict[Cell, Cell] = {}
    best_cost: dict[Cell, float] = {start: 0.0}
    counter = 0
    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))
        row, column = current
        for neighbor in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
            next_row, next_column = neighbor
            if not (0 <= next_row < height and 0 <= next_column < width):
                continue
            cell_cost = float(cost_grid[next_row][next_column])
            if cell_cost >= obstacle_cost:
                continue
            new_cost = best_cost[current] + max(cell_cost, 0.0) + 1.0
            if new_cost < best_cost.get(neighbor, math.inf):
                best_cost[neighbor] = new_cost
                came_from[neighbor] = current
                counter += 1
                heapq.heappush(frontier, (new_cost + heuristic(neighbor), counter, neighbor))
    return []


def detections_to_cost_grid(detections: Iterable[object], grid_shape: tuple[int, int]) -> list[list[float]]:
    """Integration point for Model 2 to grid conversion."""
    del detections
    rows, columns = grid_shape
    if rows <= 0 or columns <= 0:
        raise ValueError("grid_shape must contain positive dimensions")
    return [[0.0 for _ in range(columns)] for _ in range(rows)]
