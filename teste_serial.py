
from protocols import SerialHandler
import time

serial = SerialHandler("/dev/ttyAMA2", 9600)

def main():
    print("Testando!")

    while True:
        leitura = serial.read()
        
        if (leitura):
            print(leitura)
            time.sleep(5)

            serial.send('{"v": 1, "src": "central", "dst": "CC:7B:5C:4F:CD:09", "type": "register_response", "ts": 1754413674, "payload": {"status": "already_registered", "device_id": "ESP_Blink"}}')

            print("Enviado!")




if __name__ == "__main__":
    main()
