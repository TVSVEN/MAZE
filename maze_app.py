"""Tkinter interface for the keys-and-doors maze solver."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from maze_solver import Grid, generate_maze, read_grid_csv, shortest_path, write_grid_csv

PAIR_COLORS = {
    "a": "#4f8bd6", "b": "#a16bd2", "c": "#e29a32",
    "d": "#20a293", "e": "#dc6688", "f": "#829a39",
}
WHITE, BLACK, GREEN, RED, PATH = "#ffffff", "#20242a", "#45ad62", "#dc4c4c", "#f5d65c"


class MazeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Maze with Keys and Doors")
        root.minsize(700, 560)
        self.grid: Grid = []
        self.route: list[tuple[int, int]] = []
        self.revealed = 0
        self.playing = False
        self.cell_size = 34

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Size").pack(side="left")
        self.size_var = tk.IntVar(value=15)
        ttk.Spinbox(top, from_=5, to=40, width=4, textvariable=self.size_var).pack(side="left", padx=(4, 12))
        ttk.Label(top, text="Key/door pairs").pack(side="left")
        self.keys_var = tk.IntVar(value=3)
        ttk.Spinbox(top, from_=1, to=5, width=3, textvariable=self.keys_var).pack(side="left", padx=4)
        ttk.Button(top, text="Generate", command=self.generate).pack(side="left", padx=4)
        ttk.Button(top, text="Open CSV", command=self.open_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Solve", command=self.solve).pack(side="left", padx=4)
        self.play_btn = ttk.Button(top, text="▶ Play", command=self.toggle_play)
        self.play_btn.pack(side="left", padx=4)
        ttk.Button(top, text="Save path CSV", command=self.save_csv).pack(side="left", padx=4)

        body = ttk.Frame(root, padding=(10, 0, 10, 10))
        body.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(body, background="#eceff1", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        side = ttk.Frame(body, padding=12, width=170)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        ttk.Label(side, text="KEY INVENTORY", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.inventory = ttk.Label(side, text="No keys", justify="left")
        self.inventory.pack(anchor="w", pady=(8, 16))
        ttk.Label(side, text="LEGEND", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        for label, color in (("Open", WHITE), ("Wall", BLACK), ("Start", GREEN), ("Exit", RED), ("Path", PATH)):
            self.legend_item(side, label, color)
        for letter, color in PAIR_COLORS.items():
            if letter == "e":
                continue
            self.legend_item(side, f"Key {letter} / Door {letter.upper()}", color)
        self.status = tk.StringVar(value="Generate a maze or open a CSV file.")
        ttk.Label(root, textvariable=self.status, padding=(10, 4)).pack(fill="x")
        self.generate()

    @staticmethod
    def legend_item(parent, label, color):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        tk.Label(row, background=color, width=2, relief="solid", borderwidth=1).pack(side="left", padx=(0, 6))
        ttk.Label(row, text=label).pack(side="left")

    def generate(self):
        try:
            self.grid = generate_maze(int(self.size_var.get()), int(self.keys_var.get()))
            self.route = []
            self.revealed = 0
            self.playing = False
            self.play_btn.configure(text="▶ Play")
            self.status.set("Random maze generated. Press Solve to find the shortest route.")
            self.draw()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("Cannot generate maze", str(exc))

    def open_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return
        try:
            self.grid = read_grid_csv(filename)
            self.size_var.set(len(self.grid))
            self.route = []
            self.revealed = 0
            self.playing = False
            self.status.set(f"Loaded {filename}")
            self.draw()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot open maze", str(exc))

    def solve(self):
        if not self.grid:
            return
        self.route = shortest_path(self.grid) or []
        self.revealed = 0
        self.playing = False
        self.play_btn.configure(text="▶ Play")
        if not self.route:
            self.status.set("No path to the exit. Shortest path length: -1.")
            messagebox.showinfo("No path", "The exit cannot be reached with the available keys.")
        else:
            self.status.set(f"Shortest path: {len(self.route) - 1} steps. Press Play to animate it.")
            # Show the complete solved route immediately. Play then animates
            # the active position and the key/door state along that route.
            self.revealed = 0
        self.draw()

    def toggle_play(self):
        if not self.route:
            self.solve()
        if not self.route:
            return
        if self.revealed >= len(self.route):
            self.revealed = 0
        self.playing = not self.playing
        self.play_btn.configure(text="⏸ Pause" if self.playing else "▶ Play")
        if self.playing:
            self.animate()

    def animate(self):
        if not self.playing:
            return
        if self.revealed < len(self.route):
            self.revealed += 1
            self.update_inventory()
            self.draw()
            self.root.after(150, self.animate)
        else:
            self.playing = False
            self.play_btn.configure(text="▶ Play")
            self.status.set(f"Arrived at the exit in {len(self.route) - 1} steps.")

    def update_inventory(self):
        keys = set()
        for r, c in self.route[:self.revealed]:
            if self.grid[r][c] in "abcdef":
                keys.add(self.grid[r][c])
        self.inventory.configure(text="\n".join(f"●  {k}   {k.upper()} unlocked" for k in sorted(keys)) or "No keys")

    def draw(self):
        self.canvas.delete("all")
        n = len(self.grid)
        if not n:
            return
        self.canvas.update_idletasks()
        available_w = max(300, self.canvas.winfo_width() - 24)
        available_h = max(300, self.canvas.winfo_height() - 24)
        self.cell_size = max(12, min(42, available_w // n, available_h // n))
        extent = n * self.cell_size
        ox = max(10, (self.canvas.winfo_width() - extent) // 2)
        oy = max(10, (self.canvas.winfo_height() - extent) // 2)
        visited = set(self.route[:self.revealed])
        path_cells = set(self.route)
        inventory = {self.grid[r][c] for r, c in visited if self.grid[r][c] in "abcdef"}
        current = self.route[self.revealed - 1] if self.route and self.revealed else None
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                x1, y1 = ox + c * self.cell_size, oy + r * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = (GREEN if cell == "S" else RED if cell == "E" else BLACK if cell == "#"
                         else PAIR_COLORS[cell.lower()] if cell.lower() in PAIR_COLORS else WHITE)
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#aeb5bb", width=1)
                if (r, c) in path_cells and cell not in "SE":
                    self.canvas.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2, fill=PATH, outline="")
                key_collected = cell in "abcdef" and cell in inventory
                door_opened = cell in "ABCDF" and cell.lower() in inventory and (r, c) in visited
                if key_collected:
                    # Collected keys disappear from the maze; inventory keeps
                    # their identity visible.
                    self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text="✓", fill="#16854a",
                                            font=("Segoe UI", max(8, self.cell_size // 2), "bold"))
                elif door_opened:
                    self.canvas.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                                                 fill=WHITE, outline="")
                    self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text="✓", fill="#16854a",
                                            font=("Segoe UI", max(8, self.cell_size // 2), "bold"))
                elif cell in "SE" or cell in "abcdefABCDEF":
                    fg = "white" if cell in "SE" else "#17202a"
                    self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=cell, fill=fg,
                                            font=("Segoe UI", max(8, self.cell_size // 2), "bold"))
                if current == (r, c):
                    radius = max(3, self.cell_size // 6)
                    self.canvas.create_oval((x1+x2)/2-radius, (y1+y2)/2-radius,
                                            (x1+x2)/2+radius, (y1+y2)/2+radius,
                                            fill="#1769d2", outline="white", width=1)
        self.update_inventory()

    def save_csv(self):
        if not self.grid:
            return
        if not self.route:
            self.solve()
        if not self.route:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
                                               initialfile="maze_solution.csv")
        if filename:
            write_grid_csv(self.grid, filename, self.route)
            self.status.set(f"Path-marked CSV saved to {filename}")


def main():
    root = tk.Tk()
    MazeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
