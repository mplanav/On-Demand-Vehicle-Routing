from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple
import heapq
import json
import socketio
import uvicorn
import asyncio

# 
#

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Clase para el update map ---
class cellUpdate(BaseModel):
    cell: Tuple[int, int]
##
##class Car:
##    def __init__(self, index: int, position: Tuple[int, int], isFree: bool = True):
##        self.index = index
##        self.position = position
##        self.isFree = isFree

##    def __repr__(self):
##        return {
##            "index": self.index,
##           "position": self.position,
##            "isFree": self.isFree
##        }
##

# configuracion de socketio 
sio = socketio.AsyncServer(async_mode='asgi')
app.mount("/socket.io", socketio.ASGIApp(sio, socketio_path='/'))

directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]

# --- Funciones ---
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def read_map_json(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    walls = set(map(tuple, data["walls"]))
    tracks = set(map(tuple, data.get("tracks", [])))
    rfids = list(map(tuple, data.get("rfids", [])))
    width = data.get("width", 20)
    height = data.get("height", 20)
    return walls, tracks, rfids, width, height

def init_grid(width, height):
    grid = {}
    for x in range(width):
        for y in range(height):
            neighbors = []
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    neighbors.append((nx, ny))
            grid[(x, y)] = neighbors
    return grid

class DStarLite:
    def __init__(self, start, goal, walls, tracks, width, height):
        self.start = start
        self.goal = goal
        self.width = width
        self.height = height
        self.tracks = tracks
        self.km = 0
        self.grid = init_grid(width, height)
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

        is_diagonal = abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1
        base_cost = 1.4 if is_diagonal else 1

        # Penalizar mucho los movimientos fuera de tracks
        if self.tracks and b not in self.tracks:
            return base_cost * 5  # Muy caro fuera de track

        return base_cost  # Barato dentro del track



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
                return path
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

# --- Variables globales ---
planner = None
walls = set()
rfids = set()
tracks = set()
start = None
goal = None
width = 0
height = 0

# --- cargar mapa ---
walls, tracks, rfids, width, height = read_map_json("mapa.json")

# --- Rutas FastAPI ---
@app.get("/map")
async def get_map():
    if not planner:
        raise HTTPException(status_code=400, detail="Planner no inicializado")
    path = planner.get_path()
    return {
        "width": width,
        "height": height,
        "walls": list(walls),
        "tracks": list(tracks),
        "rfids": rfids,
        "start": planner.start,
        "goal": goal,
        "path": path,
        "visited": list(planner.visited)
    }

@app.post("/update-map")
async def update_map(data: cellUpdate):
    global planner, walls

    cell = tuple(data.cell)

    old_walls = set(walls)
    if cell in walls:
        walls.remove(cell)
    else:
        walls.add(cell)

    changed_cells = old_walls.symmetric_difference(walls)
    planner.km += heuristic(planner.start, planner.start)
    planner.walls = walls

    for cell in changed_cells:
        planner.g[cell] = float('inf')
        planner.rhs[cell] = float('inf')
        planner.update_vertex(cell)
        for neighbor in planner.grid[cell]:
            planner.update_vertex(neighbor)

    planner.compute_shortest_path()

    return JSONResponse(content={"message": "Mapa actualizado"})

@app.post("/step")
async def step():
    global planner, goal

    if not planner:
       raise HTTPException(status_code=400, detail="Planner no inicializado")

    path = planner.get_path()
    next_pos = planner.move_start(path)

    if next_pos is None or next_pos == goal:
        return {
            "finished": True,
            "start": planner.start,
            "path": path,
            "visited": list(planner.visited)
        }

    planner.km += heuristic(planner.start, next_pos)
    planner.start = next_pos
    planner.compute_shortest_path()

    return {
        "start": planner.start,
        "path": planner.get_path(),
        "visited": list(planner.visited),
        "finished": False
    }

# --- WebSocket ---
@app.websocket("/path")
async def websocket_path(websocket: WebSocket):
    global planner, walls, start, goal, width, height

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            start_positions = [tuple(pos) for pos in data.get("start", [])]
            goal = tuple(data.get("goal"))
            new_wall = tuple(data.get("new_wall")) if "new_wall" in data else None

            if not start_positions:
                await websocket.send_json({
                    "type": "error",
                    "event": "path",
                    "error": "No se han proporcionado posiciones de inicio"
                })
                return

            def manhattan(a, b):
                return abs(a[0] - b[0]) + abs(a[1] - b[1])

            best_start = min(start_positions, key=lambda s: manhattan(s, goal))
            car_index = start_positions.index(best_start)

            dynamic_walls = set(walls)
            for other_start in start_positions:
                if other_start != best_start:
                    dynamic_walls.add(other_start)

            planner = DStarLite(best_start, goal, dynamic_walls, tracks, width, height)
            planner.compute_shortest_path()
            best_path = planner.get_path()

            if not best_path or best_path[-1] != goal:
                await websocket.send_json({
                    "type": "error",
                    "event": "path",
                    "error": "No hay camino disponible desde la posición más cercana"
                })
                return


            if new_wall:
                walls.add(new_wall)

                async def remove_wall(wall):
                    await asyncio.sleep(4)
                    walls.discard(wall)

                asyncio.create_task(remove_wall(new_wall))

            await websocket.send_json({
                "type": "success",
                "event": "path",
                "path": best_path,
                "car": car_index
            })

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "event": "path",
            "error": str(e)
        })
    finally:
        await websocket.close()




@app.post("/reset")
async def reset():
    global planner
    planner = None
    return {"message": "Planner reseteado"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)



#   "start" : {position: [x,y], isFree: true/False},
#           {position: [x,y], isFree: true/False},
#   "goal" : {position: [x,y]}
#