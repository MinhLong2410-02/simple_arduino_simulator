import asyncio
import websockets
import json
import time
import sys

class ArduinoClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.data_buffer = []
        
    async def connect(self):
        """Kết nối đến Arduino WebSocket Server"""
        try:
            print("🔌 Connecting to Arduino...")
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print("✅ Connected to Arduino successfully!")
            
            # Đợi Arduino khởi động (giống time.sleep(2) trong code gốc)
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
        return True
    
    async def disconnect(self):
        """Ngắt kết nối"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("📡 Disconnected from Arduino")
    
    async def send_command(self, command):
        """Gửi lệnh đến Arduino"""
        if not self.connected:
            print("❌ Not connected to Arduino!")
            return None
            
        try:
            await self.websocket.send(json.dumps(command))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            print(f"❌ Error sending command: {e}")
            return None
    
    async def read_sensor_data(self):
        """Đọc dữ liệu cảm biến (mô phỏng ser.readline())"""
        # Đọc temperature sensor (A0)
        temp_response = await self.send_command({
            "type": "analogRead",
            "pin": 0
        })
        
        # Đọc light sensor (A1) 
        light_response = await self.send_command({
            "type": "analogRead",
            "pin": 1
        })
        
        if temp_response and light_response:
            # Chuyển đổi giá trị analog thành string giống Arduino serial
            temp_value = temp_response.get("value", 0)
            light_value = light_response.get("value", 0)
            
            # Mô phỏng format dữ liệu Arduino gửi qua serial
            data1 = f"TEMP:{temp_value/10:.1f}"  # Temperature in Celsius
            data2 = f"LIGHT:{light_value}"       # Light sensor raw value
            
            return data1, data2
        
        return None, None
    
    async def continuous_read(self):
        """Đọc dữ liệu liên tục (mô phỏng while loop trong code gốc)"""
        i = 0
        
        print("📊 Starting continuous sensor reading...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Đọc dữ liệu cảm biến (giống ser.readline() x2)
                data1, data2 = await self.read_sensor_data()
                
                if data1 and data2:
                    # In dữ liệu giống code gốc (chỉ in khi i%2 == 1)
                    if i % 2 == 1:
                        print(f"{data1}, {data2}", end="\r")
                    
                    i += 1
                    
                    # Reset counter khi đạt 1000 (giống code gốc)
                    if i == 1000:
                        i = 0
                        print("\n🔄 Counter reset to 0")
                
                # Delay nhỏ để không spam quá nhiều requests
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        except Exception as e:
            print(f"\n❌ Error during reading: {e}")

# Phiên bản đồng bộ giống code Arduino gốc
class ArduinoSerialSimulator:
    def __init__(self, port="ws://localhost:8765", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.client = ArduinoClient(port)
        self.connected = False
    
    def connect(self):
        """Kết nối đồng bộ"""
        async def _connect():
            return await self.client.connect()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_connect())
        self.connected = result
        return result
    
    def readline(self):
        """Đọc một dòng dữ liệu (mô phỏng ser.readline())"""
        async def _read():
            return await self.client.read_sensor_data()
        
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_read())
    
    def close(self):
        """Đóng kết nối"""
        async def _close():
            await self.client.disconnect()
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_close())

# Hàm main mô phỏng code Arduino gốc
async def main_arduino_style():
    """Mô phỏng chính xác code Arduino gốc"""
    # Tương đương: ser = serial.Serial('COM7', 9600)
    arduino = ArduinoClient("ws://localhost:8765")
    
    # Kết nối
    if not await arduino.connect():
        return
    
    # Tương đương: time.sleep(2) # Đợi Arduino khởi động
    await asyncio.sleep(2)
    
    i = 0
    
    try:
        while True:
            # Tương đương: data1 = ser.readline().decode().strip()
            # Tương đương: data2 = ser.readline().decode().strip()
            data1, data2 = await arduino.read_sensor_data()
            
            if data1 and data2:
                # Tương đương: if i%2 == 1: print(data1 + ", " + data2, end="\r")
                if i % 2 == 1:
                    print(data1 + ", " + data2, end="\r")
                
                i += 1
                
                # Tương đương: if i == 1000: i = 0
                if i == 1000:
                    i = 0
            
            await asyncio.sleep(0.1)  # Delay nhỏ
            
    except KeyboardInterrupt:
        print("\n🛑 Program stopped")
    finally:
        await arduino.disconnect()

# Menu lựa chọn
async def interactive_menu():
    """Menu tương tác"""
    arduino = ArduinoClient()
    
    while True:
        print("\n" + "="*50)
        print("🔧 Arduino WebSocket Client")
        print("="*50)
        print("1. Connect to Arduino")
        print("2. Read single sensor data")
        print("3. Continuous reading (Arduino style)")
        print("4. Control LEDs")
        print("5. Disconnect")
        print("0. Exit")
        print("-"*50)
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            await arduino.connect()
            
        elif choice == "2":
            if arduino.connected:
                data1, data2 = await arduino.read_sensor_data()
                if data1 and data2:
                    print(f"📊 Sensor Data: {data1}, {data2}")
            else:
                print("❌ Please connect first!")
                
        elif choice == "3":
            if arduino.connected:
                await arduino.continuous_read()
            else:
                print("❌ Please connect first!")
                
        elif choice == "4":
            if arduino.connected:
                print("\nLED Control:")
                print("1. Toggle Built-in LED")
                print("2. Toggle Red LED")
                print("3. Blink Built-in LED")
                
                led_choice = input("Choose LED action: ").strip()
                
                if led_choice == "1":
                    response = await arduino.send_command({
                        "type": "digitalWrite",
                        "pin": 13,
                        "value": True
                    })
                    print(f"✅ {response.get('message', 'Done')}")
                elif led_choice == "2":
                    response = await arduino.send_command({
                        "type": "digitalWrite", 
                        "pin": 8,
                        "value": True
                    })
                    print(f"✅ {response.get('message', 'Done')}")
                elif led_choice == "3":
                    response = await arduino.send_command({
                        "type": "blink_builtin",
                        "times": 5,
                        "delay": 500
                    })
                    print(f"⚡ {response.get('message', 'Blinking...')}")
            else:
                print("❌ Please connect first!")
                
        elif choice == "5":
            await arduino.disconnect()
            
        elif choice == "0":
            if arduino.connected:
                await arduino.disconnect()
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    print("🔧 Arduino WebSocket Client")
    print("Choose mode:")
    print("1. Arduino-style continuous reading")
    print("2. Interactive menu")
    
    mode = input("Enter mode (1 or 2): ").strip()
    
    try:
        if mode == "1":
            # Chạy giống hệt code Arduino gốc
            asyncio.run(main_arduino_style())
        else:
            # Chạy menu tương tác
            asyncio.run(interactive_menu())
    except KeyboardInterrupt:
        print("\n👋 Program terminated by user")