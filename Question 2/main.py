def fill(grid, n, total, rows):
    """Recursively place number n, then n+1, ... until total."""
    if n > total:
        return
    col = (n - 1) // rows              # which column
    j = (n - 1) % rows                 # position within the column
    row = rows - 1 - j if col % 2 == 0 else j   # up on even cols, down on odd
    slant = int(2 * j / (rows - 1) + 0.5) if rows > 1 else 0
    x = 5 * col + slant
    grid[row][x:x + 2] = list(f"{n:02d}")
    fill(grid, n + 1, total, rows)


def print_grid(grid, r=0):
    """Recursively print each row."""
    if r == len(grid):
        return
    print("".join(grid[r]).rstrip())
    print_grid(grid, r + 1)


def main():
    rows = int(input("rows: "))
    cycles = int(input("cycles: "))
    total = rows * cycles * 2
    width = 10 * cycles + 3
    grid = [[" "] * width for _ in range(rows)]
    fill(grid, 1, total, rows)
    print_grid(grid)


main()