/* USER CODE BEGIN PV */
// --- Configuración de Calibración ---
// Cambia este valor cuando tengas la estructura física.
// Por ahora, asumimos que 4096 pasos es una vuelta completa del eje motor.
#define PASOS_POR_VUELTA 4096 

// Secuencia Half-Step (8 pasos) para suavidad y torque
const uint8_t sequence[8][4] = {
  {1,0,0,0}, {1,1,0,0}, {0,1,0,0}, {0,1,1,0},
  {0,0,1,0}, {0,0,1,1}, {0,0,0,1}, {1,0,0,1}
};

// Variables de Estado (Volatile es vital para interrupciones)
volatile int32_t pasos_restantes_horiz = 0;
volatile int32_t pasos_restantes_vert = 0;

// Índices de paso actuales (0-7)
volatile int8_t idx_h = 0;
volatile int8_t idx_vL = 0;
volatile int8_t idx_vR = 0;
/* USER CODE END PV */

/* USER CODE BEGIN PFP */

// Función auxiliar para escribir en los pines
void stepper_write(int motor_id, int step_index) {
    // Asegurar rango 0-7
    uint8_t* p = (uint8_t*)sequence[step_index % 8];
    
    if(motor_id == 0) { // Horizontal (PA0-PA3)
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, p[0]);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, p[1]);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_2, p[2]);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_3, p[3]);
    }
    else if(motor_id == 1) { // Vertical L (PA4-PA7)
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, p[0]);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, p[1]);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, p[2]);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_7, p[3]);
    }
    else if(motor_id == 2) { // Vertical R (PB0, PB1, PB2, PB10)
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, p[0]);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_1, p[1]);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_2, p[2]);
        HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10, p[3]);
    }
}

// Funciones Públicas para Mover (No bloqueantes)
void Mover_Horizontal(int32_t pasos) {
    pasos_restantes_horiz = pasos; // + Derecha, - Izquierda
}

void Mover_Vertical(int32_t pasos) {
    pasos_restantes_vert = pasos;  // + Arriba, - Abajo
}

// Callback del Timer (El corazón del movimiento)
// Se ejecuta automáticamente cada X ms (ej. 1ms)
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
    if (htim->Instance == TIM2) {
        
        // --- Motor Horizontal ---
        if (pasos_restantes_horiz != 0) {
            int8_t dir = (pasos_restantes_horiz > 0) ? 1 : -1;
            idx_h = (idx_h + 8 + dir) % 8;
            stepper_write(0, idx_h);
            pasos_restantes_horiz -= dir;
        }

        // --- Motores Verticales (Sincronizados) ---
        if (pasos_restantes_vert != 0) {
            int8_t dir = (pasos_restantes_vert > 0) ? 1 : -1; // 1=Subir, -1=Bajar
            
            // Lógica de Espejo:
            // Para subir, Motor L gira CW (+1), Motor R gira CCW (-1)
            // Para bajar, Motor L gira CCW (-1), Motor R gira CW (+1)
            
            int8_t dir_L = dir; 
            int8_t dir_R = -dir; // INVERTIDO para el lado opuesto
            
            idx_vL = (idx_vL + 8 + dir_L) % 8;
            idx_vR = (idx_vR + 8 + dir_R) % 8;
            
            stepper_write(1, idx_vL); // Motor L
            stepper_write(2, idx_vR); // Motor R
            
            pasos_restantes_vert -= dir;
        }
        
        // Apagado de seguridad (opcional): Si no hay pasos, poner pines en 0 para no calentar
        // (Se omite aquí por brevedad, pero es recomendable agregar un timeout)
    }
}
/* USER CODE END PFP */

/* USER CODE BEGIN 2 */
HAL_TIM_Base_Start_IT(&htim2); // ¡No olvides iniciar el timer!
/* USER CODE END 2 */

/* USER CODE BEGIN WHILE */
while (1)
{
    // --- ZONA DE PRUEBAS Y CALIBRACIÓN ---
    // Tu compañera solo necesita descomentar esto para probar
    
    // Prueba 1: Mover Horizontal 1 vuelta
    Mover_Horizontal(PASOS_POR_VUELTA);
    HAL_Delay(2000); // Esperar a que termine (aprox)
    
    // Prueba 2: Mover Vertical (Subir) media vuelta
    // Ambos motores deberían girar en sentidos opuestos
    Mover_Vertical(PASOS_POR_VUELTA / 2);
    HAL_Delay(2000);
    
    // Prueba 3: Regresar todo a "Cero"
    Mover_Horizontal(-PASOS_POR_VUELTA);
    Mover_Vertical(-(PASOS_POR_VUELTA / 2));
    
    HAL_Delay(5000); // Pausa larga antes de repetir
    
    /* USER CODE END WHILE */
}