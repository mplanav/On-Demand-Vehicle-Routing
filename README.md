
# 📍 API de Pathfinding con FastAPI y D* Lite

Este proyecto proporciona una API basada en FastAPI que implementa el algoritmo D* Lite para planificación de rutas en un mapa dinámico. También incluye soporte para comunicación en tiempo real usando WebSockets y `socket.io`.

---

## 🧱 Estructura del Proyecto

```
.
├── app/
│   ├── main.py               # API principal con rutas HTTP y WebSocket
│   ├── requirements.txt      # Dependencias Python
│   └── mapa.json             # Mapa estático con muros, pistas y RFIDs
├── Dockerfile                # Imagen para entorno de producción
├── docker-compose.yml        # Orquestación del contenedor
└── README.md                 # Este archivo
```

---

## 🚀 Cómo Ejecutar el Proyecto

### Requisitos

- Docker
- Docker Compose

### Paso 1: Construir y levantar los contenedores

```bash
docker-compose up --build
```

Esto ejecutará la aplicación en `http://localhost:5000`.

> El contenedor se reiniciará automáticamente (`restart: always`) y expondrá el puerto 5000.

---

## 🧠 Cómo Funciona

### 🔧 Endpoints REST

| Método | Ruta           | Descripción |
|--------|----------------|-------------|
| GET    | `/map`         | Devuelve el estado actual del mapa, ruta, visitados, etc. |
| POST   | `/update-map`  | Permite modificar el mapa (añadir o quitar paredes). |
| POST   | `/step`        | Avanza un paso hacia el objetivo y devuelve el estado. |
| POST   | `/reset`       | Reinicia el planificador (`planner`). |

#### Formato de `/update-map`

```json
{
  "cell": [x, y]
}
```

---

### 🔌 WebSocket: `/path`

Permite enviar una solicitud de ruta desde múltiples posiciones de inicio hacia un destino objetivo. La API seleccionará el punto más cercano y devolverá la mejor ruta posible.

#### 🔁 Formato del mensaje WebSocket

```json
{
  "start": [[x1, y1], [x2, y2], ..., [xN, yN]],
  "goal": [gx, gy]
}
```

- Hasta 10 puntos de inicio.
- Todos los puntos deben estar sobre un `track` o `rfid` del mapa (`mapa.json`).
- Puede incluir opcionalmente: `"new_wall": [wx, wy]`.

#### 📥 Respuesta WebSocket (éxito)

```json
{
  "type": "success",
  "event": "path",
  "path": [[x, y], [x2, y2], ...],
  "car": 2
}
```

#### ❌ Respuesta WebSocket (error)

```json
{
  "type": "error",
  "event": "path",
  "error": "Descripción del problema"
}
```

---

## 🗺️ Formato del archivo `mapa.json`

Contiene:

- `"walls"`: Paredes que bloquean el camino.
- `"tracks"`: Celdas por donde pueden circular los vehículos (preferidas).
- `"rfids"`: Puntos válidos para inicio/objetivo.
- `"width"` y `"height"`: Dimensiones del mapa.

Ejemplo:
```json
{
  "walls": [[1,1], [2,2]],
  "tracks": [[3,3], [3,4]],
  "rfids": [[3,3]],
  "width": 20,
  "height": 20
}
```

---

## ⚙️ Desarrollo y Hot Reload

El contenedor usa `--reload` para recargar automáticamente los cambios en el código.

Puedes montar el volumen de desarrollo (`./app:/app`) para trabajar localmente con reflejo instantáneo en el contenedor.

---

## 📦 Dependencias Principales

- `fastapi`
- `uvicorn`
- `pydantic`
- `asyncio`
- `python-socketio`

---

## 🧪 Ejemplo de Uso con `websocat`

```bash
websocat ws://localhost:5000/path
```

Mensaje:
```json
{"start": [[22, 16], [23, 16]], "goal": [22, 30]}
```

---

## 🔁 Docker Tips

- Construir manualmente:
  ```bash
  docker build -t api_pathfinding .
  ```

- Ejecutar sin `docker-compose`:
  ```bash
  docker run -p 5000:5000 api_pathfinding
  ```

---

## 🧼 Reiniciar el Planificador

Puedes usar el endpoint `/reset` para reiniciar el estado del planificador:

```bash
curl -X POST http://localhost:5000/reset
```

---

## 📄 Licencia

MIT - Puedes usar, modificar y distribuir este software libremente.

---

## ✨ Autor

Desarrollado por Marc Plana.
