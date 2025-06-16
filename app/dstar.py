import heapq
import os
import time

# Direcciones en 8 direcciones
directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def read_map(filename):
    with open(filename, "r") as f:
        lines = f.read().splitlines()
    walls = set()
    for y, line in enumerate(lines):
        for x, c in enumerate(line.strip().split()):
            if c == '#':
                walls.add((x, y))
            elif c == 'S':
                start = (x, y)
            elif c == 'G':
                goal = (x, y)
    return walls, start, goal

def init_grid(size):
    grid = {}
    for x in range(size):
        for y in range(size):
            neighbors = []
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    neighbors.append((nx, ny))
            grid[(x, y)] = neighbors
    return grid

class DStarLite:
    def __init__(self, start, goal, walls, size):
        self.start = start
        self.goal = goal
        self.size = size
        self.km = 0
        self.grid = init_grid(size)
        self.g = {}
        self.rhs = {}
        self.U = []
        self.walls = walls
        self.visited = set()

        for node in self.grid:
            self.g[node] = float('inf')
            self.rhs[node] = float('inf')
        self.rhs[goal] = 0
        heapq.heappush(self.U, (self.calculate_key(goal), goal))

    def calculate_key(self, s):
        return (min(self.g[s], self.rhs[s]) + heuristic(self.start, s) + self.km, min(self.g[s], self.rhs[s]))

    def update_vertex(self, u):
        if u != self.goal:
            self.rhs[u] = min(
                [self.g[succ] + self.cost(u, succ) for succ in self.grid[u] if succ not in self.walls]
            )
        self.U = [(k, n) for (k, n) in self.U if n != u]
        heapq.heapify(self.U)
        if self.g[u] != self.rhs[u]:
            heapq.heappush(self.U, (self.calculate_key(u), u))

    def cost(self, a, b):
        if b in self.walls:
            return float('inf')
        return 1.4 if abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1 else 1

    def compute_shortest_path(self):
        while self.U and (self.U[0][0] < self.calculate_key(self.start) or self.rhs[self.start] != self.g[self.start]):
            k_old, u = heapq.heappop(self.U)
            k_new = self.calculate_key(u)
            if k_old < k_new:
                heapq.heappush(self.U, (k_new, u))
            elif self.g[u] > self.rhs[u]:
                self.g[u] = self.rhs[u]
                for pred in self.grid[u]:
                    if pred not in self.walls:
                        self.update_vertex(pred)
            else:
                self.g[u] = float('inf')
                for pred in self.grid[u] + [u]:
                    if pred not in self.walls:
                        self.update_vertex(pred)

    def get_path(self):
        path = [self.start]
        current = self.start
        while current != self.goal:
            neighbors = [n for n in self.grid[current] if n not in self.walls]
            if not neighbors:
                break
            next_node = min(neighbors, key=lambda n: self.g.get(n, float('inf')) + self.cost(current, n))
            if self.g.get(next_node, float('inf')) == float('inf') or next_node in path:
                break
            current = next_node
            path.append(current)
        return path

    def move_start(self, path):
        if len(path) > 1:
            self.start = path[1]
            self.visited.add(self.start)
            return self.start
        return None

def print_map(size, walls, start, goal, path, visited):
    for y in range(size):
        row = ""
        for x in range(size):
            pos = (x, y)
            if pos == start:
                row += "S "
            elif pos == goal:
                row += "G "
            elif pos in walls:
                row += "# "
            elif pos in path:
                row += "* "
            elif pos in visited:
                row += "o "
            else:
                row += ". "
        print(row)
    print()

def main():
    size = 11
    last_map = None
    planner = None
    current_start = None

    while True:
        try:
            walls, original_start, goal = read_map("mapa.txt")
        except:
            print("Error leyendo mapa.txt. Esperando...")
            time.sleep(2)
            continue

        if planner is None:
            current_start = original_start
            planner = DStarLite(current_start, goal, walls, size)
            planner.compute_shortest_path()
        else:
            if frozenset(walls) != frozenset(planner.walls):
                print("Mapa modificado. Propagando cambios...")
                old_walls = planner.walls
                planner.walls = walls
                changed_cells = old_walls.symmetric_difference(walls)

                planner.km += heuristic(planner.start, current_start)

                for cell in changed_cells:
                    planner.g[cell] = float('inf')
                    planner.rhs[cell] = float('inf')
                    planner.update_vertex(cell)
                    for neighbor in planner.grid[cell]:
                        planner.update_vertex(neighbor)

                planner.compute_shortest_path()

        # ActualizaciÃ³n obligatoria aunque no cambie el mapa
        planner.km += heuristic(planner.start, current_start)
        planner.start = current_start
        planner.compute_shortest_path()

        path = planner.get_path()
        if not path or planner.g.get(path[-1], float('inf')) == float('inf'):
            print("No hay ruta disponible hacia el objetivo.")
            break

        print_map(size, walls, planner.start, goal, path, planner.visited)

        next_pos = planner.move_start(path)
        if next_pos is None or next_pos == goal:
            print("Llegamos al objetivo.")
            break

        current_start = next_pos

        time.sleep(2)
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()
