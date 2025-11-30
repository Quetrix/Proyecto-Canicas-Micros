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

[cite_start]La comunicación entre el Microprocesador (Raspberry Pi) y el Microcontrolador (STM32) se realiza a través del protocolo **Serial Asíncrono (UART)**, cumpliendo con el requisito del proyecto de usar RS-232[cite: 101].

| Parámetro | Configuración del STM32 | Función |
| :--- | :--- | :--- |
| **Protocolo** | USART2 (VCP) | Comunicación bidireccional por el cable USB. |
| **Baud Rate** | 115200 | Velocidad de transferencia de datos. |
| **Pines** | PA2 (TX), PA3 (RX) | Pasan a través del puente ST-LINK V2.1. |
| **Terminador** | Carácter `\n` (Line Feed) | El STM32 procesa la orden solo después de recibir este carácter. |

### Protocolo de Comando
El STM32 espera comandos en el formato **[Comando][Pasos]**, terminado con `\n`.
* **Horizontal:** `H` o `h` (Ej: `H2048`, `h-1000`)
* **Vertical:** `V` o `v` (Ej: `V1000`, `v-500`)

## 4. Consideraciones Eléctricas

* **Tierra Común (GND):** El negativo de la fuente de alimentación externa de 5V para los drivers debe estar conectado al **GND** de la placa Nucleo.
* **Inversión de Giro:** La inversión de dirección para el movimiento nivelado de la plataforma Vertical se maneja por **software** para el Motor M2, aunque la conexión física se ajustó para lograr la oposición inicial.