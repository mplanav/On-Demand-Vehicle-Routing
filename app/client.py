import websockets
import asyncio

async def connect_to_websocket():
    uri = "ws://0.0.0.0:5000/path"  # Asegúrate de usar 'ws://'
    async with websockets.connect(uri) as websocket:
        # Envía datos al servidor WebSocket
        data = {
            "start": [[1, 1], [2, 2]],  # ejemplo de datos de inicio
            "goal": [3, 3]              # ejemplo de datos de destino
        }
        await websocket.send_json(data)

        # Recibe la respuesta del servidor WebSocket
        response = await websocket.recv()
        print(response)

asyncio.run(connect_to_websocket())