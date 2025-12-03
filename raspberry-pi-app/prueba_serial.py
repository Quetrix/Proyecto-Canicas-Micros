import serial
import time

# --- CONFIGURACIÓN SERIAL ---
# 1. Identificamos el puerto correcto para la Raspberry Pi
PORT_NAME = '/dev/ttyACM0' 
# 2. Usamos la misma velocidad que configuraste en el STM32
BAUD_RATE = 115200 

def enviar_comando(comando):
    """Envía un comando serial al STM32."""
    
    # CRÍTICO: El comando debe terminar en '\n'
    mensaje = comando.strip() + '\n'
    
    try:
        # Abrir el puerto serial
        ser = serial.Serial(PORT_NAME, BAUD_RATE, timeout=0.1)
        
        # Esperar un momento para que la conexión se estabilice
        time.sleep(0.1) 
        
        # Enviar el comando codificado en bytes (UTF-8)
        ser.write(mensaje.encode('utf-8'))
        print(f"✅ Enviado: {comando.strip()}")
        
        # Cerrar el puerto
        ser.close()

    except serial.SerialException as e:
        print(f"❌ Error de conexión serial: {e}")
        print("Asegúrate de que el STM32 esté conectado y que el puerto no esté abierto en otra aplicación.")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")


# --- BUCLE DE PRUEBA INTERACTIVO ---
print("--- TEST DE COMANDOS STM32 ---")
print("Protocolo:")
print("  - Motores: H[pasos] o V[pasos]. Ej: H4096, V-2000")
print("  - Servo:   S[angulo]. Ej: S45, S0, S90")
print(" CUIDADO: Si el servo esta en la estructura, moverlo entre 25 y 65 grados")

while True:
    try:
        # Usamos input() para capturar el comando
        comando = input("Comando a enviar (o 'q' para salir): ").strip()
        
        if comando.lower() == 'q':
            break
        
        if comando:
            enviar_comando(comando)
            
    except KeyboardInterrupt:
        break
    
print("Prueba finalizada.")