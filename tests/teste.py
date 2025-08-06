import serial
import json
import time

test_msg = {
    "v": 1,
    "src": "central",
    "dst": "48:55:19:00:04:1E",
    "type": "command",
    "ts": int(time.time()),
    "payload": {
            "status": "registered",
            "led": 1
    }
}

ser = serial.Serial('/dev/ttyAMA2', 9600)
ser.write((json.dumps(test_msg) + '\n').encode('utf-8'))