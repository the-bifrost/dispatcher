from utils.registry import DeviceRegistry

def main():
    registry = DeviceRegistry("/home/thalesmartins/batata.json")

    registry.add(device_id="teste", address="127.0.0.1", protocol="IP", teste2="teste2", parametrodonada="parametro xuxu beleza")

if __name__ == "__main__":
    main()

