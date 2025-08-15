import asyncio
import websockets
import json
from datetime import datetime
import random

# Trạng thái của Arduino simulator
arduino_state = {
    "leds": {
        "built_in": False,  # Pin 13 - LED built-in
        "red": False,       # Pin 8 - LED đỏ
        "green": False,     # Pin 9 - LED xanh lá
        "blue": False,      # Pin 10 - LED xanh dương
        "yellow": False     # Pin 11 - LED vàng
    },
    "sensors": {
        "temperature": 25.0,
        "light": 512,
        "potentiometer": 0
    },
    "pins": {
        "analog": [0] * 6,  # A0-A5
        "digital": [False] * 14  # D0-D13
    }
}

# Lưu trữ các kết nối client
connected_clients = set()

async def handle_client(websocket):
    """Xử lý kết nối từ Arduino IDE Simulator"""
    print(f"Arduino IDE kết nối từ {websocket.remote_address}")
    
    connected_clients.add(websocket)
    
    try:
        # Gửi trạng thái hiện tại của Arduino
        welcome_msg = {
            "type": "arduino_ready",
            "message": "Arduino Uno R3 Simulator Ready",
            "board": "Arduino Uno R3",
            "firmware": "1.8.19",
            "timestamp": datetime.now().isoformat(),
            "state": arduino_state
        }
        await websocket.send(json.dumps(welcome_msg))
        
        # Lắng nghe lệnh từ client
        async for message in websocket:
            print(f"Arduino nhận lệnh: {message}", end = '\r')
            
            try:
                data = json.loads(message)
                response = await process_arduino_command(data)
                await websocket.send(json.dumps(response))
                
                # Broadcast trạng thái mới đến tất cả clients
                if response.get("broadcast", False):
                    await broadcast_message(json.dumps({
                        "type": "state_update",
                        "state": arduino_state,
                        "timestamp": datetime.now().isoformat()
                    }), exclude=websocket)
                    
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(error_response))
                
    except websockets.exceptions.ConnectionClosed:
        print(f"Arduino IDE {websocket.remote_address} đã ngắt kết nối")
    except Exception as e:
        print(f"Lỗi xử lý Arduino: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"Số Arduino IDE đang kết nối: {len(connected_clients)}")

async def process_arduino_command(data):
    """Xử lý lệnh Arduino"""
    command_type = data.get("type", "")
    
    if command_type == "digitalWrite":
        pin = data.get("pin")
        value = data.get("value", False)
        
        # Cập nhật trạng thái LED
        if pin == 13:
            arduino_state["leds"]["built_in"] = value
        elif pin == 8:
            arduino_state["leds"]["red"] = value
        elif pin == 9:
            arduino_state["leds"]["green"] = value
        elif pin == 10:
            arduino_state["leds"]["blue"] = value
        elif pin == 11:
            arduino_state["leds"]["yellow"] = value
            
        # Cập nhật pin digital
        if 0 <= pin <= 13:
            arduino_state["pins"]["digital"][pin] = value
            
        return {
            "type": "digitalWrite_response",
            "pin": pin,
            "value": value,
            "status": "success",
            "message": f"Pin {pin} set to {'HIGH' if value else 'LOW'}",
            "timestamp": datetime.now().isoformat(),
            "broadcast": True
        }
        
    elif command_type == "digitalRead":
        pin = data.get("pin", 0)
        value = arduino_state["pins"]["digital"][pin] if 0 <= pin <= 13 else False
        
        return {
            "type": "digitalRead_response",
            "pin": pin,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        
    elif command_type == "analogRead":
        pin = data.get("pin", 0)
        
        # Mô phỏng cảm biến
        if pin == 0:  # Temperature sensor
            arduino_state["sensors"]["temperature"] = round(random.uniform(20, 35), 1)
            value = int(arduino_state["sensors"]["temperature"] * 10)
        elif pin == 1:  # Light sensor
            arduino_state["sensors"]["light"] = random.randint(0, 1023)
            value = arduino_state["sensors"]["light"]
        elif pin == 2:  # Potentiometer
            arduino_state["sensors"]["potentiometer"] = random.randint(0, 1023)
            value = arduino_state["sensors"]["potentiometer"]
        else:
            value = arduino_state["pins"]["analog"][pin] if 0 <= pin <= 5 else 0
            
        return {
            "type": "analogRead_response",
            "pin": pin,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        
    elif command_type == "blink_builtin":
        # Nhấp nháy LED built-in
        times = data.get("times", 3)
        delay = data.get("delay", 500)
        
        return {
            "type": "blink_response",
            "message": f"Blinking built-in LED {times} times",
            "times": times,
            "delay": delay,
            "timestamp": datetime.now().isoformat(),
            "broadcast": True
        }
        
    elif command_type == "reset_arduino":
        # Reset Arduino
        arduino_state["leds"] = {k: False for k in arduino_state["leds"]}
        arduino_state["pins"]["digital"] = [False] * 14
        
        return {
            "type": "reset_response",
            "message": "Arduino đã được reset",
            "state": arduino_state,
            "timestamp": datetime.now().isoformat(),
            "broadcast": True
        }
        
    elif command_type == "get_state":
        return {
            "type": "state_response",
            "state": arduino_state,
            "timestamp": datetime.now().isoformat()
        }
        
    else:
        return {
            "type": "error",
            "message": f"Unknown command: {command_type}",
            "timestamp": datetime.now().isoformat()
        }

async def broadcast_message(message, exclude=None):
    """Gửi tin nhắn đến tất cả Arduino IDEs"""
    if connected_clients:
        recipients = connected_clients.copy()
        if exclude:
            recipients.discard(exclude)
            
        await asyncio.gather(
            *[client.send(message) for client in recipients],
            return_exceptions=True
        )

async def sensor_simulation():
    """Mô phỏng cảm biến thay đổi theo thời gian"""
    while True:
        await asyncio.sleep(5)  # Cập nhật mỗi 5 giây
        
        # Cập nhật cảm biến
        arduino_state["sensors"]["temperature"] += random.uniform(-0.5, 0.5)
        arduino_state["sensors"]["temperature"] = max(15, min(40, arduino_state["sensors"]["temperature"]))
        
        arduino_state["sensors"]["light"] += random.randint(-50, 50)
        arduino_state["sensors"]["light"] = max(0, min(1023, arduino_state["sensors"]["light"]))
        
        # Broadcast cập nhật cảm biến
        if connected_clients:
            sensor_update = {
                "type": "sensor_update",
                "sensors": arduino_state["sensors"],
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_message(json.dumps(sensor_update))

async def main():
    """Khởi động Arduino Simulator Server"""
    print("🔧 Arduino Uno R3 Simulator Server Starting...")
    print("📡 Server listening at ws://localhost:8765")
    print("🚀 Ready to connect with Arduino IDE Simulator")
    
    # Chạy server và sensor simulation
    async with websockets.serve(handle_client, "localhost", 8765):
        await sensor_simulation()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔴 Arduino Simulator Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")