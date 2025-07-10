from utils.envelope import *

def main():
    envelope = make_envelope(src="teste", dst="thales", payload={"state":"on"})
    print(f"Envelope: {envelope}")

    envelope_serial = serialize(envelope)
    print(f"Envelope Serial: {envelope_serial}")

    envelope_dict = deserialize(envelope_serial)
    print(f"Envelope Dict: {envelope_dict}")

    print(f"Envelope Dict Inválido: {serialize(True)}")
    print(f"Envelope JSON String Inválido: {deserialize(True)}")

if __name__ == "__main__":
    main()
