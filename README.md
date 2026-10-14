# Maze with Keys and Doors

A complete Python solution with a Tkinter visualizer, CSV import/export, a BFS shortest-path solver, and a random maze generator that guarantees a solvable route.

## Browser version (no installation)

Open `maze_web.html` in Chrome, Edge, or another modern browser. It is a standalone web app and works offline. Generate or load a maze, solve it, animate the result, and download the path-marked CSV. You can keep the HTML file and reopen it any time. The web version supports up to five distinct key/door pairs because the assignment reserves `E` for the exit.

## Requirements

- Python 3.10 or newer
- Tkinter (included with most Windows Python installations)
- No third-party packages

## Run the visual application

Open this folder in VS Code, then run in its terminal:

```powershell
python maze_app.py
```

Use **Generate** to create a random maze, **Open CSV** to load a maze, **Solve** to display its shortest path, **Play** to animate the route, and **Save path CSV** to export it. Path cells are marked by appending `x` to their original cell symbols (for example `a` becomes `ax`), so keys and doors stay identifiable. The exported CSV is an annotation for viewing; load the original maze CSV to solve it again.

**Format limitation:** `E` denotes the exit, so the format cannot also unambiguously represent a door for key `e`. The generator uses the other five door labels (`A`, `B`, `C`, `D`, `F`) and supports up to five pairs. To use six pairs, the assignment format needs a distinct exit symbol (for example `X`) or a distinct door label for `e`.

## CSV format

Use one grid row per CSV record and one cell per field. Example:

```csv
S,.,.,#,.,.,.
#,#,.,#,.,#,#
a,.,.,.,.,A,.
#,#,#,#,.,#,.
.,.,.,.,.,#,.
.,#,#,#,.,.,.
.,.,.,#,.,.,E
```

Cells are `.`, `#`, `S`, `E`, keys `a` through `f`, or matching doors `A` through `F`. The grid must be square, with exactly one start and exit; every door must have a corresponding key. For the most reliable CSV round-trip, keep one cell per field. The reader also accepts one-character compact rows.

## Command-line solver

Solve a CSV and write the path-marked output:

```powershell
python maze_solver.py example_maze.csv --output maze_solution.csv
```

Generate, solve, and export a random 20×20 maze with four pairs:

```powershell
python maze_solver.py --size 20 --keys 4 --output maze_solution.csv
```

Add `--seed 123` to reproduce a generated maze. The program prints the shortest path length, or `-1` if no path exists. The generator supports up to five pairs because `E` is reserved for the exit.

## Source files

- `maze_solver.py` — validation, CSV I/O, BFS solver, and random generator.
- `maze_app.py` — interactive colored grid, inventory, path animation, and file dialogs.
- `example_maze.csv` — sample input maze.
