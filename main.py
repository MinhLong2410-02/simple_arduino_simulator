import asyncio
import websockets
import json
import time

async def main():
    try:
        # Kết nối WebSocket (thay cho serial.Serial('COM7', 9600))
        uri = "ws://localhost:8765"
        websocket = await websockets.connect(uri)
        print("Connected to Arduino!")
        
        # Đợi Arduino khởi động
        time.sleep(2)
    
        i = 0
        
        while True:
            # Đọc temperature (data1)
            await websocket.send(json.dumps({"type": "analogRead", "pin": 0}))
            response1 = await websocket.recv()
            resp1 = json.loads(response1)
            data1 = resp1.get("value", 0)
            
            # Đọc light sensor (data2) 
            await websocket.send(json.dumps({"type": "analogRead", "pin": 1}))
            response2 = await websocket.recv()
            resp2 = json.loads(response2)
            data2 = resp2.get("value", 0)
            
            # In kết quả giống code gốc
            if i % 2 == 1:
                print(f"{data1}, {data2}", end="\r")
            
            i += 1
            if i == 1000:
                i = 0
            
            time.sleep(0.1)

    except Exception as e:
        print(f"Error: {e}")
        
asyncio.run(main())