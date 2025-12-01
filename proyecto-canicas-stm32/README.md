# ⚙️ Conexiones y Protocolo de Control (STM32 Nucleo-F446RE)

Este documento detalla el mapeo de pines utilizado y el protocolo de comunicación implementado para controlar el circuito vertical de canicas.

## 1. Diagrama de Referencia

Para ubicar los pines en la placa, consulte el diagrama de pinout:

![Pinout de la placa Nucleo-F446RE](pinout.png)

## 2. Mapeo de Pines para Actuadores

Los 12 pines del microcontrolador están configurados como **GPIO Output** y conectados a los 12 pines de entrada de los drivers ULN2003.

| Motor | Bobina del Motor | Pin del Microcontrolador (STM32) | Pin Arduino (Etiqueta de la Placa) | Conector del Driver |
| :--- | :--- | :--- | :--- | :--- |
| **Horizontal (M0)** | Bobina 1-4 | PA0, PA1, PA4, PB0 | A0, A1, A2, A3 | IN1, IN2, IN3, IN4 |
| **Vertical Izquierdo (M1)**| Bobina 1-4 | PA5, PA6, PA7, PA8 | D13, D12, D11, D7 | IN1, IN2, IN3, IN4 |
| **Vertical Derecho (M2)** | Bobina 1-4 | **PB4, PA10, PB3, PB1** | **D5, D2, D3, D14** | IN1, IN2, IN3, IN4 |

## 3. Comunicación Serial (UART / RS-232)

El STM32 está configurado para escuchar órdenes asíncronas de la Raspberry Pi (RPi) a través del cable USB (Virtual COM Port).

### 3.1. Configuración de Conexión (Lado RPi)
Para abrir la comunicación desde Python (usando la librería `pySerial`), se deben usar los siguientes parámetros:

* **Puerto:** `/dev/ttyACM0` (Verificar con `ls /dev/ttyACM*` en la terminal).
* **Baud Rate (Velocidad):** `115200`
* **Permisos:** El usuario `micropenes` debe tener permisos para usar el grupo `dialout`.

### 3.2. Protocolo de Comandos (Lado STM32)

El microcontrolador espera un comando en el formato **[Comando][Pasos]**, **TERMINADO OBLIGATORIAMENTE con un salto de línea (`\n`)**.

| Comando | Formato | Descripción |
| :--- | :--- | :--- |
| **Horizontal** | `H` o `h` + número | Mueve el motor Horizontal. El valor positivo es Derecha, el negativo es Izquierda. |
| **Vertical** | `V` o `v` + número | Mueve los motores Verticales (M1 y M2) de forma sincronizada. El valor positivo es Arriba (Subir), el negativo es Abajo (Bajar). |
| **Ejemplo** | `H2048` | Mueve el motor Horizontal 2048 pasos hacia la derecha. |

**Nota Crítica:** El carácter `\n` es la señal que el STM32 usa para saber que el comando ha finalizado. En Python, esto se logra enviando la cadena seguida de `\n` (e.g., `ser.write("H2048\n".encode('utf-8'))`).


## 4. Consideraciones Eléctricas

* **Tierra Común (GND):** El negativo de la fuente de alimentación externa de 5V para los drivers debe estar conectado al **GND** de la placa Nucleo.
* **Inversión de Giro:** La inversión de dirección para el movimiento nivelado de la plataforma Vertical se maneja por **software** para el Motor M2, aunque la conexión física se ajustó para lograr la oposición inicial.