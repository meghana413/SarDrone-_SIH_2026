"""A* pathfinding over a hazard-aware cost grid."""
from __future__ import annotations

import heapq
import math
from typing import Iterable, Sequence

Grid = Sequence[Sequence[float]]
Cell = tuple[int, int]


def victim_cells_from_detections(
    detections: Iterable[object], grid_shape: tuple[int, int], *, frame_shape: tuple[int, int] | None = None
) -> list[Cell]:
    """Return unique victim cells as ``(row, column)`` for the planner."""
    rows, columns = grid_shape
    if rows <= 0 or columns <= 0:
        raise ValueError("grid shape must contain positive dimensions")
    frame_rows, frame_columns = frame_shape or (rows, columns)
    if frame_rows <= 0 or frame_columns <= 0:
        raise ValueError("frame_shape must contain positive dimensions")

    cells: list[Cell] = []
    for detection in detections:
        if detection is None:
            continue
        if isinstance(detection, dict):
            class_name, bbox = str(detection.get("class_name", "")).lower(), detection.get("bbox")
            if class_name != "victim" or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                continue
            center_x = (float(bbox[0]) + float(bbox[2])) / 2.0
            center_y = (float(bbox[1]) + float(bbox[3])) / 2.0
        else:
            if str(getattr(detection, "class_name", "")).lower() != "victim":
                continue
            center_x = (float(getattr(detection, "x1")) + float(getattr(detection, "x2"))) / 2.0
            center_y = (float(getattr(detection, "y1")) + float(getattr(detection, "y2"))) / 2.0
        column = max(0, min(columns - 1, int(round(center_x * (columns - 1) / max(frame_columns - 1, 1)))))
        row = max(0, min(rows - 1, int(round(center_y * (rows - 1) / max(frame_rows - 1, 1)))))
        if (row, column) not in cells:
            cells.append((row, column))
    return cells


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


def detections_to_cost_grid(
    detections: Iterable[object], grid: tuple[int, int] | list[list[float]], *, frame_shape: tuple[int, int] | None = None
) -> list[list[float]]:
    """Map victim bounding-box centres from pixels into planner grid cells.

    Victim cells remain traversable because they are the A* goals; the caller
    selects one of these mapped cells as the goal instead of blindly routing to
    the far corner. ``frame_shape`` is ``(height, width)`` and is required for
    correct conversion from camera pixels (it defaults to grid dimensions for
    callers already supplying grid-space coordinates).
    """
    if isinstance(grid, tuple):
        rows, columns = grid
        if rows <= 0 or columns <= 0:
            raise ValueError("grid shape must contain positive dimensions")
        cost_grid = [[0.0 for _ in range(columns)] for _ in range(rows)]
    else:
        if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
            raise ValueError("grid must be a non-empty rectangular list")
        cost_grid = grid
        rows, columns = len(cost_grid), len(cost_grid[0])

    for y_index, x_index in victim_cells_from_detections(detections, (rows, columns), frame_shape=frame_shape):
        # Explicitly materialise the victim's grid cell as a priority marker.
        # ``find_path`` clamps grid costs to zero or above, so this marker is
        # traversable when the selected victim is used as the goal rather than
        # becoming an obstacle that makes the rescue target unreachable.
        cost_grid[y_index][x_index] = -1.0

    return cost_grid
