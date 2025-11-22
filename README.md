🏗️ Circuito Vertical de Canicas - Proyecto Mecatrónico
Este repositorio contiene el código fuente, documentación y simulaciones para el Sistema de Distribución de Canicas. El sistema transporta canicas a través de una matriz vertical de 3x3 espacios controlada por un microcontrolador y un microprocesador.

🧩 Arquitectura del Sistema
El proyecto se divide en dos cerebros principales:

Cerebro (Lógica e Interfaz): Raspberry Pi corriendo Python. Se encarga de la interfaz de usuario (GUI), la máquina de estados y el cálculo de rutas.

Músculo (Control en Tiempo Real): STM32 corriendo C (HAL). Se encarga de mover los motores paso a paso con precisión, leer la celda de carga y manejar sensores mediante interrupciones.

Hardware Principal
Microcontrolador: STM32 Nucleo.

Microprocesador: Raspberry Pi 3/4.

Actuadores: 3x Motores Stepper 28BYJ-48 (5V) con drivers ULN2003.
            1x Motor DC 5V.
            1x Servomotor.

Sensores: 1x Celda de Carga 10kg + Amplificador HX711 para conteo de canicas.