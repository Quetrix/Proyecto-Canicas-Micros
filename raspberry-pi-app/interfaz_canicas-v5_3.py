import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import threading

# --- CONFIGURACION SERIAL ---
PORT_NAME = '/dev/ttyACM0' 
BAUD_RATE = 115200

# --- CONFIGURACION FISICA ---
STEPS_H = 1536
STEPS_V = 1408

# Ajuste fino (1/8)
CALIB_FINE_H = int(STEPS_H / 8)
CALIB_FINE_V = int(STEPS_V / 8)

# --- TIEMPOS DE ESPERA (Segundos) ---
# Como el motor va lento (2000-1), aumentamos los tiempos de espera
# Ajusta estos valores si sientes que el sistema espera demasiado o muy poco.
TIME_MOVE_H = 4.5  
TIME_MOVE_V = 5.0 
TIME_SERVO  = 1.5

class MarbleInterfaceFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE CONTROL V5.4 - RETORNO POR IZQUIERDA")
        self.root.geometry("1024x600")
        self.root.configure(bg="#1e293b") 

        # --- ESTADO DEL SISTEMA ---
        self.ser = None
        self.connect_serial()
        
        self.posicion_actual = "S1"
        self.columna_virtual_destino = 1 
        
        self.rutas_programadas = {} 
        self.contador_canicas = 0 
        
        # Bandera para detener secuencias
        self.stop_emergencia = False
        
        # Mapa Logico
        self.mapa_coords = {
            "S1": (0,0), "S2": (0,1), "S3": (0,2),
            1: (1,0), 2: (1,1), 3: (1,2),
            4: (2,0), 5: (2,1), 6: (2,2),
            7: (3,0), 8: (3,1), 9: (3,2),
            "Destino": (4,1)
        }

        self.setup_ui()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(PORT_NAME, BAUD_RATE, timeout=0.1)
            time.sleep(2) 
            print("CONEXION SERIAL OK")
        except Exception:
            print("MODO SIMULACION (Sin Serial)")

    def enviar_comando(self, cmd):
        try:
            if self.ser and self.ser.is_open:
                msg = f"{cmd}\n"
                self.ser.write(msg.encode('utf-8'))
                print(f"TX: {msg.strip()}")
            else:
                print(f"SIM: {cmd}")
        except Exception as e:
            print(f"Error Serial: {e}")

    # --- LOGICA STOP EMERGENCIA ---
    def activar_stop(self):
        self.stop_emergencia = True
        print("!!! STOP ACTIVADO !!!")
        
        self.enviar_comando("H0")
        self.enviar_comando("V0") 
        self.enviar_comando("S65") 
        
        messagebox.showwarning("STOP", "PARADA DE EMERGENCIA ACTIVADA.\nMotores detenidos.")
        self.stop_emergencia = False

    # --- LOGICA DE MOVIMIENTO ---
    def calcular_comando(self, origen, destino):
        r1, c1 = self.mapa_coords[origen]
        
        if origen == "Destino":
            r1 = 4
            c1 = self.columna_virtual_destino
        
        if destino == "Destino":
            r2 = 4
            if origen in [7, 8, 9]:
                _, c_temp = self.mapa_coords[origen]
                c2 = c_temp
            else:
                c2 = 1 
        else:
            r2, c2 = self.mapa_coords[destino]

        diff_r = r2 - r1
        diff_c = c2 - c1
        
        if diff_r == 1 and diff_c == 0: return f"V-{STEPS_V}"
        if diff_r == -1 and diff_c == 0: return f"V{STEPS_V}"
        if diff_c == 1 and diff_r == 0: return f"H{STEPS_H}"
        if diff_c == -1 and diff_r == 0: return f"H-{STEPS_H}"
        
        if diff_c == 0 and diff_r > 1:
            pasos_total = diff_r * STEPS_V
            return f"V-{pasos_total}" 

        return None 

    def validar_movimiento(self, origen, destino):
        if destino == "Destino":
            if origen in [7, 8, 9]: return True, "OK"
            return False, "A Destino solo se baja desde 7, 8 o 9"

        r1, c1 = self.mapa_coords[origen]
        r2, c2 = self.mapa_coords[destino]
        
        if abs(r1-r2) + abs(c1-c2) != 1:
            return False, "Movimiento no adyacente"
        
        if r2 < r1:
            return False, "No se puede subir en ruta"
            
        return True, "OK"

    # --- THREADING ---
    def ejecutar_movimiento_thread(self, destino, callback=None):
        if self.stop_emergencia: return
        threading.Thread(target=self._proceso_mover, args=(destino, callback)).start()

    def _proceso_mover(self, destino, callback):
        if self.stop_emergencia: return
        
        cmd = self.calcular_comando(self.posicion_actual, destino)
        if cmd:
            self.enviar_comando(cmd)
            
            # Determinar tiempo de espera segun el eje
            wait_time = TIME_MOVE_V if "V" in cmd else TIME_MOVE_H
            if "V-" in cmd and int(cmd.split('-')[1]) > STEPS_V: 
                 # Si baja varios pisos de golpe, dar mas tiempo
                 wait_time = wait_time * 2.5 

            if destino == "Destino":
                _, c_origen = self.mapa_coords[self.posicion_actual]
                self.columna_virtual_destino = c_origen
            
            self.posicion_actual = destino
            self.root.after(0, self.actualizar_grid_visual)
            
            # Espera activa chequeando STOP
            steps_wait = int(wait_time * 10)
            for _ in range(steps_wait): 
                if self.stop_emergencia: return
                time.sleep(0.1)
            
            if callback and not self.stop_emergencia:
                self.root.after(0, callback)

    # --- INTERFAZ UI ---
    def setup_ui(self):
        for widget in self.root.winfo_children(): widget.destroy()

        header = tk.Frame(self.root, bg="#0f172a", height=60)
        header.pack(fill="x")
        tk.Label(header, text="CONTROL DE CANICAS V5.4", font=("Arial", 20, "bold"), 
                 bg="#0f172a", fg="#e2e8f0").pack(side="left", padx=20, pady=10)
        
        tk.Button(header, text="STOP TOTAL", bg="#dc2626", fg="white", font=("Arial", 12, "bold"),
                  command=self.activar_stop).pack(side="right", padx=20, pady=10)

        self.main_frame = tk.Frame(self.root, bg="#1e293b")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.mostrar_menu_principal()

    def mostrar_menu_principal(self):
        for w in self.main_frame.winfo_children(): w.destroy()
        
        tk.Label(self.main_frame, text="MENU PRINCIPAL", font=("Arial", 18), 
                 bg="#1e293b", fg="white").pack(pady=30)

        btn_opts = {"width": 30, "height": 2, "font": ("Arial", 14, "bold"), "bg": "#334155", "fg": "white"}
        
        tk.Button(self.main_frame, text="1. MODO MANUAL", command=self.iniciar_modo_manual, **btn_opts).pack(pady=10)
        tk.Button(self.main_frame, text="2. MODO PROGRAMADO", command=self.iniciar_modo_programado, **btn_opts).pack(pady=10)
        tk.Button(self.main_frame, text="3. CALIBRACION Y NIVELACION", command=self.iniciar_modo_calibracion, **btn_opts).pack(pady=10)

    def construir_pantalla_base(self, titulo, mostrar_grid=True):
        for w in self.main_frame.winfo_children(): w.destroy()
        
        top = tk.Frame(self.main_frame, bg="#334155")
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text=titulo, font=("Arial", 14, "bold"), bg="#334155", fg="#facc15").pack(side="left", padx=10)
        tk.Button(top, text="MENU", bg="#64748b", fg="white", command=self.mostrar_menu_principal).pack(side="right", padx=10, pady=5)

        self.panel_izq = tk.Frame(self.main_frame, bg="#1e293b", width=550)
        self.panel_izq.pack(side="left", fill="y", padx=10)
        
        if mostrar_grid:
            self.panel_der = tk.Frame(self.main_frame, bg="#0f172a")
            self.panel_der.pack(side="right", fill="both", expand=True, padx=10)
            self.construir_grid_visual()
        else:
            self.panel_der = None 

        self.lbl_canicas = tk.Label(self.panel_izq, text=f"Canicas: {self.contador_canicas}", 
                                    font=("Arial", 16, "bold"), bg="#1e293b", fg="#facc15")
        self.lbl_canicas.pack(side="bottom", pady=20)

    # --- MODO 3: CALIBRACION AVANZADA ---
    def iniciar_modo_calibracion(self):
        self.construir_pantalla_base("CALIBRACION Y MANTENIMIENTO", mostrar_grid=False)
        
        # 1. Servo
        tk.Label(self.panel_izq, text="CONTROL SERVO", bg="#1e293b", fg="#fbbf24", font=("Arial", 10, "bold")).pack(pady=(10,5))
        frame_servo = tk.Frame(self.panel_izq, bg="#1e293b")
        frame_servo.pack()
        tk.Button(frame_servo, text="ABRIR", command=lambda: self.enviar_comando("S25"), bg="#d97706", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(frame_servo, text="CERRAR", command=lambda: self.enviar_comando("S65"), bg="#059669", fg="white", width=10).pack(side="left", padx=5)

        # 2. General
        tk.Label(self.panel_izq, text="MOVIMIENTO GENERAL (1 CELDA)", bg="#1e293b", fg="#fbbf24", font=("Arial", 10, "bold")).pack(pady=(20,5))
        frame_gros = tk.Frame(self.panel_izq, bg="#1e293b")
        frame_gros.pack()
        
        tk.Button(frame_gros, text="▲", command=lambda: self.mover_calib("V", 1, "FULL"), bg="#475569", fg="white", width=4, height=2).grid(row=0, column=1)
        tk.Button(frame_gros, text="◀", command=lambda: self.mover_calib("H", -1, "FULL"), bg="#475569", fg="white", width=4, height=2).grid(row=1, column=0, padx=5)
        tk.Button(frame_gros, text="▶", command=lambda: self.mover_calib("H", 1, "FULL"), bg="#475569", fg="white", width=4, height=2).grid(row=1, column=2, padx=5)
        tk.Button(frame_gros, text="▼", command=lambda: self.mover_calib("V", -1, "FULL"), bg="#475569", fg="white", width=4, height=2).grid(row=2, column=1)

        # 3. Fino
        tk.Label(self.panel_izq, text="AJUSTE FINO (1/8)", bg="#1e293b", fg="#fbbf24", font=("Arial", 10, "bold")).pack(pady=(20,5))
        frame_fino = tk.Frame(self.panel_izq, bg="#1e293b")
        frame_fino.pack()
        
        # M2 (IZQ)
        f_m2 = tk.Frame(frame_fino, bg="#334155", padx=5, pady=5)
        f_m2.grid(row=0, column=0, padx=5)
        tk.Label(f_m2, text="M2(IZQ)", bg="#334155", fg="white", font=("Arial", 8)).pack()
        tk.Button(f_m2, text="▲", command=lambda: self.mover_individual("R", 1), bg="#3b82f6", fg="white").pack(pady=2)
        tk.Button(f_m2, text="▼", command=lambda: self.mover_individual("R", -1), bg="#3b82f6", fg="white").pack(pady=2)

        # AMBOS VERTICALES
        f_v = tk.Frame(frame_fino, bg="#475569", padx=5, pady=5)
        f_v.grid(row=0, column=1, padx=5)
        tk.Label(f_v, text="VERT(2)", bg="#475569", fg="white", font=("Arial", 8, "bold")).pack()
        tk.Button(f_v, text="▲▲", command=lambda: self.mover_calib("V", 1, "FINE"), bg="#8b5cf6", fg="white").pack(pady=2)
        tk.Button(f_v, text="▼▼", command=lambda: self.mover_calib("V", -1, "FINE"), bg="#8b5cf6", fg="white").pack(pady=2)

        # HORIZONTAL
        f_h = tk.Frame(frame_fino, bg="#334155", padx=5, pady=5)
        f_h.grid(row=0, column=2, padx=5)
        tk.Label(f_h, text="HORIZ", bg="#334155", fg="white", font=("Arial", 8)).pack()
        tk.Button(f_h, text="◀", command=lambda: self.mover_calib("H", -1, "FINE"), bg="#3b82f6", fg="white").pack(pady=2)
        tk.Button(f_h, text="▶", command=lambda: self.mover_calib("H", 1, "FINE"), bg="#3b82f6", fg="white").pack(pady=2)

        # M1 (DER)
        f_m1 = tk.Frame(frame_fino, bg="#334155", padx=5, pady=5)
        f_m1.grid(row=0, column=3, padx=5)
        tk.Label(f_m1, text="M1(DER)", bg="#334155", fg="white", font=("Arial", 8)).pack()
        tk.Button(f_m1, text="▲", command=lambda: self.mover_individual("L", 1), bg="#3b82f6", fg="white").pack(pady=2)
        tk.Button(f_m1, text="▼", command=lambda: self.mover_individual("L", -1), bg="#3b82f6", fg="white").pack(pady=2)

        tk.Button(self.panel_izq, text="CONFIRMAR POSICION S1", bg="#10b981", fg="white", 
                  command=self.confirmar_s1).pack(pady=20, fill="x")

    def mover_calib(self, eje, dir, tipo):
        pasos = CALIB_FINE_V if tipo == "FINE" else STEPS_V
        if eje == "H" and tipo == "FINE": pasos = CALIB_FINE_H
        elif eje == "H" and tipo == "FULL": pasos = STEPS_H
            
        signo = "" if dir > 0 else "-"
        self.enviar_comando(f"{eje}{signo}{pasos}")

    def mover_individual(self, motor, dir):
        pasos = CALIB_FINE_V
        signo = "" if dir > 0 else "-"
        self.enviar_comando(f"{motor}{signo}{pasos}")

    def confirmar_s1(self):
        if messagebox.askyesno("Confirmar", "¿Posicion actual es S1?"):
            self.posicion_actual = "S1"
            self.columna_virtual_destino = 0
            messagebox.showinfo("Listo", "Sistema calibrado en S1")

    # --- MODO 1: MANUAL ---
    def iniciar_modo_manual(self):
        self.construir_pantalla_base("MODO MANUAL")
        
        pad = tk.Frame(self.panel_izq, bg="#1e293b")
        pad.pack(pady=20)
        
        tk.Button(pad, text="IZQ", command=lambda: self.accion_manual_click("left"), bg="#475569", fg="white", width=8, height=2).grid(row=1, column=0, padx=5)
        tk.Button(pad, text="ABAJO", command=lambda: self.accion_manual_click("down"), bg="#475569", fg="white", width=8, height=2).grid(row=1, column=1, padx=5)
        tk.Button(pad, text="DER", command=lambda: self.accion_manual_click("right"), bg="#475569", fg="white", width=8, height=2).grid(row=1, column=2, padx=5)

        tk.Label(self.panel_izq, text="RETORNO RAPIDO:", bg="#1e293b", fg="white").pack(pady=(20, 5))
        frame_ir = tk.Frame(self.panel_izq, bg="#1e293b")
        frame_ir.pack()
        
        for z in ["S1", "S2", "S3"]:
            tk.Button(frame_ir, text=z, command=lambda dest=z: self.iniciar_retorno_thread(dest),
                      bg="#0ea5e9", fg="white", width=5).pack(side="left", padx=2)

    def accion_manual_click(self, direccion):
        if self.stop_emergencia: return
        r, c = self.mapa_coords[self.posicion_actual]
        if self.posicion_actual == "Destino":
            r = 4
            c = self.columna_virtual_destino

        targets = {"left": (r, c-1), "right": (r, c+1), "down": (r+1, c)}
        target_coords = targets.get(direccion)
        
        destino = None
        for k, v in self.mapa_coords.items():
            if v == target_coords: destino = k; break
        
        if direccion == "down" and self.posicion_actual in [7, 8, 9]: destino = "Destino"

        if destino:
            valido, msg = self.validar_movimiento(self.posicion_actual, destino)
            if valido:
                self.ejecutar_movimiento_thread(destino, callback=self.check_fin_recorrido_manual)
            else:
                messagebox.showwarning("Movimiento Invalido", msg)
        else:
            messagebox.showwarning("Error", "No existe zona en esa direccion")

    def check_fin_recorrido_manual(self):
        if self.posicion_actual == "Destino" and not self.stop_emergencia:
            self.rutina_volcado_y_retorno()

    def rutina_volcado_y_retorno(self):
        if self.stop_emergencia: return
        messagebox.showinfo("Llegada", "Canica en Destino.\nEl sistema volcará la canasta ahora.")
        
        if self.stop_emergencia: return
        self.enviar_comando("S25")
        time.sleep(TIME_SERVO)
        if self.stop_emergencia: return
        self.enviar_comando("S65")
        time.sleep(1.0)             
        
        if not self.stop_emergencia:
            self.contador_canicas += 1
            self.lbl_canicas.config(text=f"Canicas: {self.contador_canicas}")
            # Volver por defecto a S1 tras descargar en modo manual
            self.iniciar_retorno_thread("S1")

    # --- MODO 2: PROGRAMADO ---
    def iniciar_modo_programado(self):
        self.ruta_temp = []
        self.construir_pantalla_base("PROGRAMACION", mostrar_grid=True)
        
        self.frame_lista_rutas = tk.Frame(self.panel_der, bg="#1e293b", width=200)
        self.frame_lista_rutas.pack(side="right", fill="y", padx=5)
        tk.Label(self.frame_lista_rutas, text="RUTAS", bg="#1e293b", fg="white", font=("Arial",10,"bold")).pack()
        self.refrescar_lista_rutas()
        self.fase_programacion_ui()

    def refrescar_lista_rutas(self):
        for w in self.frame_lista_rutas.winfo_children(): 
            if isinstance(w, tk.Frame): w.destroy()
        
        for k, camino in self.rutas_programadas.items():
            f = tk.Frame(self.frame_lista_rutas, bg="#334155")
            f.pack(fill="x", pady=2)
            
            txt_camino = "->".join(map(str, camino))
            lbl_text = f"{k}: {txt_camino}"
            tk.Label(f, text=lbl_text, bg="#334155", fg="#facc15", anchor="w", font=("Arial", 8)).pack(side="left", fill="x", expand=True)
            tk.Button(f, text="X", bg="#ef4444", fg="white", width=2,
                      command=lambda key=k: self.borrar_ruta(key)).pack(side="right")

    def fase_programacion_ui(self):
        for w in self.panel_izq.winfo_children(): 
            if w != self.lbl_canicas: w.destroy()

        tk.Label(self.panel_izq, text="CREAR RUTA", font=("Arial", 12, "bold"), bg="#1e293b", fg="#fbbf24").pack(pady=5)
        
        self.var_inicio = tk.StringVar(value="S1")
        frame_ini = tk.Frame(self.panel_izq, bg="#1e293b")
        frame_ini.pack()
        for z in ["S1", "S2", "S3"]:
            tk.Radiobutton(frame_ini, text=z, variable=self.var_inicio, value=z, 
                           bg="#1e293b", fg="white", selectcolor="#0f172a",
                           command=self.reset_ruta_builder).pack(side="left")

        self.lbl_ruta = tk.Label(self.panel_izq, text="...", wraplength=350, bg="#334155", fg="white")
        self.lbl_ruta.pack(pady=5, fill="x")

        frame_nums = tk.Frame(self.panel_izq, bg="#1e293b")
        frame_nums.pack()
        for i in range(1, 10):
            tk.Button(frame_nums, text=str(i), width=4, command=lambda z=i: self.agregar_paso(z)).grid(row=(i-1)//3, column=(i-1)%3, padx=2, pady=2)
        
        tk.Button(self.panel_izq, text="DESTINO", bg="#10b981", fg="white", command=lambda: self.agregar_paso("Destino")).pack(pady=5, fill="x")

        tk.Button(self.panel_izq, text="BORRAR ULTIMO", command=self.undo_paso, bg="#64748b", fg="white").pack(fill="x", pady=2)
        tk.Button(self.panel_izq, text="GUARDAR RUTA", command=self.guardar_ruta, bg="#0ea5e9", fg="white").pack(fill="x", pady=5)
        
        tk.Button(self.panel_izq, text="INICIAR RECORRIDO", command=self.iniciar_secuencia_thread,
                  bg="#d946ef", fg="white", font=("Arial", 12, "bold")).pack(fill="x", pady=20)

    def borrar_ruta(self, key):
        if messagebox.askyesno("Borrar", f"¿Eliminar ruta {key}?"):
            del self.rutas_programadas[key]
            self.refrescar_lista_rutas()

    def reset_ruta_builder(self):
        self.ruta_temp = [self.var_inicio.get()]
        self.actualizar_lbl_ruta()

    def agregar_paso(self, zona):
        if not hasattr(self, 'ruta_temp') or not self.ruta_temp: self.reset_ruta_builder()
        ultimo = self.ruta_temp[-1]
        valido, msg = self.validar_movimiento(ultimo, zona)
        if valido:
            self.ruta_temp.append(zona)
            self.actualizar_lbl_ruta()
        else:
            messagebox.showwarning("Invalido", msg)

    def undo_paso(self):
        if len(self.ruta_temp) > 1:
            self.ruta_temp.pop()
            self.actualizar_lbl_ruta()

    def actualizar_lbl_ruta(self):
        self.lbl_ruta.config(text="->".join(map(str, self.ruta_temp)))

    def guardar_ruta(self):
        if not self.ruta_temp or self.ruta_temp[-1] != "Destino":
            messagebox.showerror("Error", "Debe terminar en Destino")
            return
        inicio = self.ruta_temp[0]
        if inicio in self.rutas_programadas: del self.rutas_programadas[inicio]
        self.rutas_programadas[inicio] = self.ruta_temp[1:]
        self.refrescar_lista_rutas()
        self.reset_ruta_builder()

    def iniciar_secuencia_thread(self):
        if not self.rutas_programadas:
            messagebox.showwarning("Vacio", "No hay rutas programadas")
            return
        for w in self.panel_izq.winfo_children(): 
            if isinstance(w, tk.Button): w.config(state="disabled")
        self.stop_emergencia = False
        threading.Thread(target=self._proceso_secuencia).start()

    def _proceso_secuencia(self):
        for inicio, camino in self.rutas_programadas.items():
            if self.stop_emergencia: break
            
            # --- FASE 1: IR AL INICIO ---
            self._proceso_retorno(inicio)
            
            if self.stop_emergencia: break
            evt = threading.Event()
            self.root.after(0, lambda: self._show_info_wait("Carga", f"Coloque canica en {inicio}", evt))
            evt.wait()

            # --- FASE 2: EJECUTAR RUTA ---
            for paso in camino:
                if self.stop_emergencia: break
                self._proceso_mover(paso, None)
            
            # --- FASE 3: DESCARGA ---
            if self.stop_emergencia: break
            self.root.after(0, lambda: messagebox.showinfo("Llegada", "Volcando canica..."))
            time.sleep(1.0)
            self.enviar_comando("S25")
            time.sleep(TIME_SERVO)
            self.enviar_comando("S65")
            time.sleep(1.0)
            
            if not self.stop_emergencia:
                self.contador_canicas += 1
                self.root.after(0, lambda: self.lbl_canicas.config(text=f"Canicas: {self.contador_canicas}"))

        if not self.stop_emergencia:
            # Al terminar todo, volver a S1 para descansar
            self._proceso_retorno("S1")
            self.root.after(0, lambda: messagebox.showinfo("Fin", "Secuencia Terminada"))
        
        self.root.after(0, self.fase_programacion_ui)

    def _show_info_wait(self, title, msg, event):
        if not self.stop_emergencia:
            messagebox.showinfo(title, msg)
        event.set()

    # --- NUEVA LOGICA DE RETORNO (V5.4) ---
    def iniciar_retorno_thread(self, destino):
        if self.stop_emergencia: return
        threading.Thread(target=self._proceso_retorno, args=(destino,)).start()

    def _proceso_retorno(self, destino_final):
        # Esta funcion asegura que el retorno SIEMPRE ocurra por la izquierda (S1)
        # para aliviar la carga del motor derecho.
        if self.stop_emergencia: return
        actual = self.posicion_actual
        
        # Si ya estamos ahi, salir
        if actual == destino_final: return

        # 1. Si estamos en Destino, moverse a la IZQUIERDA (Col 0) y luego SUBIR a S1
        if actual == "Destino":
            col_virtual = self.columna_virtual_destino # Donde cayo la canasta (0, 1 o 2)
            
            # Queremos ir a Col 0 (Izquierda total)
            # Si estamos en 1 (Centro) -> Mover 1 izq
            # Si estamos en 2 (Der) -> Mover 2 izq
            pasos_a_izq = col_virtual - 0
            
            if pasos_a_izq > 0:
                # Moverse a la izquierda
                cmd = f"H-{STEPS_H * pasos_a_izq}" # H negativo es izquierda
                # Nota: Tu logica serial espera pasos de 1 celda? O totales?
                # Tu logica `calcular_comando` envia STEPS_H por celda.
                # Aqui simplificamos: movemos celda por celda para usar sleeps correctos
                
                for _ in range(pasos_a_izq):
                    self.enviar_comando(f"H-{STEPS_H}")
                    time.sleep(TIME_MOVE_H)
            
            # Ahora estamos (teoricamente) en columna 0, abajo del todo (Nivel 4)
            # Subir hasta S1 (Nivel 0) -> Son 4 subidas
            for _ in range(4):
                self.enviar_comando(f"V{STEPS_V}") # V positivo subir
                time.sleep(TIME_MOVE_V)
            
            self.posicion_actual = "S1"
            self.root.after(0, self.actualizar_grid_visual)

        # 2. Ahora que estamos en S1 (garantizado), movernos al destino final (S2 o S3)
        # Si el destino es S1, ya terminamos.
        
        _, c_curr = self.mapa_coords[self.posicion_actual] # Deberia ser (0,0)
        _, c_dest = self.mapa_coords[destino_final]
        
        # Moverse horizontalmente hasta la columna deseada
        while c_curr != c_dest:
            if self.stop_emergencia: return
            direction = 1 if c_dest > c_curr else -1 # 1=Derecha
            cmd = f"H{STEPS_H}" if direction == 1 else f"H-{STEPS_H}"
            self.enviar_comando(cmd)
            time.sleep(TIME_MOVE_H)
            c_curr += direction
            
            # Actualizar visualmente paso a paso
            temp_key = "S1"
            if c_curr == 1: temp_key = "S2"
            if c_curr == 2: temp_key = "S3"
            self.posicion_actual = temp_key
            self.root.after(0, self.actualizar_grid_visual)

        self.posicion_actual = destino_final
        self.root.after(0, self.actualizar_grid_visual)

    # --- VISUALIZACION ---
    def construir_grid_visual(self):
        self.cells = {}
        for w in self.panel_der.winfo_children(): 
            if w != self.frame_lista_rutas: w.destroy()
        
        filas = [["S1", "S2", "S3"], [1, 2, 3], [4, 5, 6], [7, 8, 9], ["Destino"]]
        for fila in filas:
            f = tk.Frame(self.panel_der, bg="#0f172a")
            f.pack(pady=10)
            for z in fila:
                w = 20 if z == "Destino" else 8
                l = tk.Label(f, text=str(z), width=w, height=3, bg="#475569", fg="white", relief="ridge", font=("Arial", 12, "bold"))
                l.pack(side="left", padx=10)
                self.cells[z] = l
        self.actualizar_grid_visual()

    def actualizar_grid_visual(self):
        for z, l in self.cells.items():
            color = "#3b82f6" if str(z).startswith("S") else "#10b981" if z=="Destino" else "#475569"
            if z == self.posicion_actual: color = "#f59e0b"
            l.config(bg=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = MarbleInterfaceFinal(root)
    root.mainloop()