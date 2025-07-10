#!/usr/bin/env python3
import serial
import time

# Configuração das UARTs
UARTS = {
    'ttyAMA5': {'port': '/dev/ttyAMA5', 'baudrate': 9600, 'enabled': True}
}

def test_uart(uart_name, port, baudrate):
    try:
        print(f"\n🔧 Testando {uart_name} ({port})...")
        
        # Configura a UART
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        
        # Mensagem de teste
        test_msg = f"TESTE {uart_name} - Raspberry Pi UART\n"
        
        # Envia dados
        print(f"📤 Enviando: {test_msg.strip()}")
        ser.write(test_msg.encode())
        
        # Tenta ler de volta (para loopback físico)
        time.sleep(0.1)
        if ser.in_waiting > 0:
            received = ser.readline().decode().strip()
            print(f"📥 Recebido: {received}")
        else:
            print("⚠️ Nenhum dado recebido (conecte TX->RX para loopback)")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro em {uart_name}: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando Teste de UARTs do Raspberry Pi 4")
    print("------------------------------------------")
    
    # Testa cada UART
    for uart_name, config in UARTS.items():
        if config['enabled']:
            success = test_uart(uart_name, config['port'], config['baudrate'])
            UARTS[uart_name]['success'] = success
    
    # Resumo
    print("\n📊 Resultados:")
    for uart_name, config in UARTS.items():
        status = "✅ OK" if config.get('success', False) else "❌ Falha"
        print(f"{uart_name}: {status}")

    print("\n💡 Dica: Conecte TX->RX entre duas UARTs para teste bidirecional!")