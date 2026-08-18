import sys
import random
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint, QSettings
from PyQt6.QtGui import QPainter, QColor, QAction, QFont

# Paleta exacta de Uni (@unicat_uni)
C_TRANSPARENT = QColor(0, 0, 0, 0)
C_OUTLINE     = QColor("#231f20")  # Delineado oscuro suave
C_WHITE       = QColor("#ffffff")  # Pelaje blanco base y mofletes
C_SHADOW      = QColor("#e2e5eb")  # Sombras suaves para el pelo blanco
C_DARK_PATCH  = QColor("#4a3525")  # Manchas marrón oscuro/tabby de orejas y cola
C_TABBY_LIGHT = QColor("#8c6d53")  # Tono secundario del pelaje marrón
C_PINK        = QColor("#ff9ebb")  # Naricita rosa y orejas internas
C_EYE         = QColor("#12130f")  # Ojos oscuros de pupila dilatada
C_SHINE       = QColor("#ffffff")  # Brillo doble de ojos
C_FOOD        = QColor("#f4a261")  # Croissant / Panecillo
C_BUBBLE_BG   = QColor("#fff0f3")  # Globo rosa pastel
C_BUBBLE_TEXT = QColor("#4a0e17")  # Texto vinotinto

# --- CLASE DE PARTÍCULAS PIXEL ART ---
class PixelParticle:
    def __init__(self, x, y, p_type):
        self.x = float(x)
        self.y = float(y)
        self.p_type = p_type  # 'HEART', 'ZZZ', 'CRUMB', 'NOTE'
        self.life = 1.0       # De 1.0 a 0.0
        
        if p_type == 'HEART':
            self.vx = random.uniform(-0.6, 0.6)
            self.vy = random.uniform(-1.5, -0.8)
            self.color = QColor("#ff4d6d")
            self.symbol = "♥"
        elif p_type == 'ZZZ':
            self.vx = random.uniform(0.2, 0.8)
            self.vy = random.uniform(-1.0, -0.5)
            self.color = QColor("#a8ded0")
            self.symbol = "z"
        elif p_type == 'CRUMB':
            self.vx = random.uniform(-1.2, 1.2)
            self.vy = random.uniform(-1.0, 0.5)
            self.color = QColor("#f4a261")
            self.symbol = "."
        elif p_type == 'NOTE':
            self.vx = random.uniform(-0.8, 0.8)
            self.vy = random.uniform(-1.8, -1.0)
            self.color = QColor("#ffd166")
            self.symbol = "♫"

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.04
        if self.p_type == 'CRUMB':
            self.vy += 0.15  # Gravedad para las migas

class RealUniTheCat(QWidget):
    def __init__(self):
        super().__init__()
        self.drag_pos = None
        self.is_dragging = False
        
        self.state = "IDLE"  
        self.frame = 0
        self.facing_right = True
        self.speech_text = ""
        
        # Partículas, Baile y Música
        self.particles = []
        self.dance_bounce = 0
        self.current_song = ""
        self.is_playing_music = False
        
        self.happiness = 100
        self.energy = 100
        self.hunger = 85
        
        self.settings = QSettings("DesktopWidgets", "RealUniTheCat")
        self.is_pinned = self.settings.value("pinned", False, type=bool)
        
        self.init_ui()
        self.restore_position()

        # Timers
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(200)

        self.music_timer = QTimer(self)
        self.music_timer.timeout.connect(self.check_mpris_music)
        self.music_timer.start(1500)

        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.pet_ai_decision)
        self.ai_timer.start(1300)

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(4000)

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(180, 180)

    def restore_position(self):
        saved_pos = self.settings.value("pos")
        if isinstance(saved_pos, QPoint):
            self.move(saved_pos)

    def save_position(self):
        self.settings.setValue("pos", self.pos())

    def show_speech(self, text, duration=2500):
        self.speech_text = text
        self.update()
        QTimer.singleShot(duration, self.clear_speech)

    def clear_speech(self):
        self.speech_text = ""
        self.update()

    def spawn_particles(self, p_type, count=3):
        for _ in range(count):
            px = random.randint(50, 110)
            py = random.randint(30, 60)
            self.particles.append(PixelParticle(px, py, p_type))

    # --- CONSULTA MPRIS / PLAYERCTL ---
    def check_mpris_music(self):
        if self.state in ["SLEEP", "DRAG"]:
            return

        try:
            cmd = ["playerctl", "metadata", "--format", "{{status}}::{{title}} - {{artist}}"]
            res = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
            
            if "::" in res:
                status, track_info = res.split("::", 1)
                if status.lower() == "playing":
                    self.is_playing_music = True
                    clean_title = track_info.strip()
                    if self.current_song != clean_title:
                        self.current_song = clean_title
                        self.show_speech(f"♫ {self.current_song[:22]}...")
                    
                    if self.state not in ["HAPPY", "EATING"]:
                        self.state = "DANCE"
                    return
        except Exception:
            pass

        self.is_playing_music = False
        if self.state == "DANCE":
            self.state = "IDLE"

    # --- DETECCIÓN DE VENTANA ACTIVA (xdotool) ---
    def jump_to_active_window(self):
        if self.is_pinned or self.is_dragging:
            return

        try:
            out = subprocess.check_output(["xdotool", "getactivewindow", "getwindowgeometry"], 
                                         stderr=subprocess.DEVNULL, text=True)
            lines = out.splitlines()
            pos_line = [l for l in lines if "Position" in l]

            if pos_line:
                x_val = int(pos_line[0].split(":")[1].split(",")[0].strip())
                y_val = int(pos_line[0].split(":")[1].split(",")[1].split()[0].strip())
                
                target_x = max(10, x_val + 40)
                target_y = max(10, y_val - self.height() + 25)
                
                self.move(target_x, target_y)
                self.show_speech("▲ ¡Arriba de la ventana! :3")
        except Exception:
            self.show_speech("No encontré ventanas cerca")

    # --- MATRIZ REAL DE UNI ---
    def get_pixel_matrix(self):
        _ = 0
        O = 1 # Outline
        W = 2 # Blanco (Pelaje)
        S = 3 # Sombra sobre el blanco
        B = 4 # Manchita café/tabby (Orejas/Cola)
        L = 5 # Café claro / detalle
        P = 6 # Rosado (Nariz / Orejas internas)
        E = 7 # Ojos oscuros
        H = 8 # Brillo de ojos
        F = 9 # Comida

        base = [
            [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
            [_,_,O,O,_,_,_,_,_,_,_,_,_,_,_,_,_,O,O,_,_,_,_,_],
            [_,O,P,B,O,_,_,_,_,_,_,_,_,_,_,_,O,B,P,O,_,_,_],
            [_,O,B,B,B,O,_,_,_,_,_,_,_,_,_,O,B,B,B,O,_,_,_],
            [O,B,B,B,B,O,O,O,O,O,O,O,O,O,O,O,B,B,B,B,O,_,_,_],
            [O,B,B,L,W,W,W,W,W,W,W,W,W,W,W,W,L,B,B,B,O,_,_,_],
            [O,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,O,_,_,_],
            [O,W,W,O,O,O,W,W,W,W,W,W,W,W,O,O,O,W,W,W,O,_,_,_],
            [O,W,O,H,H,E,O,W,W,W,W,W,W,O,H,H,E,O,W,W,O,_,_,_],
            [O,W,O,H,E,E,O,W,W,W,W,W,W,O,H,E,E,O,W,W,O,_,_,_],
            [O,W,W,O,E,E,O,W,W,P,P,W,W,O,E,E,O,W,W,W,O,_,_,_],
            [O,W,W,W,O,O,W,W,P,P,P,P,W,W,O,O,W,W,W,W,O,_,_,_],
            [_,O,W,W,W,W,W,O,W,W,W,W,O,W,W,W,W,W,W,O,_,_,_,_],
            [_,_,O,O,W,W,W,W,W,W,W,W,W,W,W,W,W,O,O,_,_,_,_,_],
            [_,_,_,O,W,W,W,W,W,W,W,W,W,W,W,W,O,_,O,O,_,_],
            [_,_,_,O,W,W,W,W,W,W,W,W,W,W,W,W,O,O,B,B,O,_,_],
            [_,_,_,O,W,W,W,W,W,W,W,W,W,W,W,W,O,B,B,L,O,_,_],
            [_,_,_,O,W,S,W,W,W,W,W,W,W,W,S,W,O,B,B,O,_,_,_],
            [_,_,_,_,O,W,W,O,O,W,W,O,O,W,W,O,_,O,O,_,_,_,_],
            [_,_,_,_,O,S,S,O,_,O,O,_,O,S,S,O,_,_,_,_,_,_,_],
            [_,_,_,_,_,O,O,_,_,_,_,_,_,O,O,_,_,_,_,_,_,_,_],
            [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
            [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
            [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
        ]

        walk = [row[:] for row in base]
        if self.frame == 1:
            walk[18] = [_,_,_,_,O,O,W,W,O,W,W,O,W,W,O,O,_,O,O,_,_,_,_]
            walk[15] = [_,_,_,O,W,W,W,W,W,W,W,W,W,W,W,W,O,O,B,B,O,O,O]
            walk[16] = [_,_,_,O,W,W,W,W,W,W,W,W,W,W,W,W,O,B,B,B,L,B,O]

        drag = [row[:] for row in base]
        drag[8]  = [O,W,O,H,H,H,O,W,W,W,W,W,W,O,H,H,H,O,W,W,O,_,_,_]
        drag[9]  = [O,W,O,H,E,E,O,W,W,W,W,W,W,O,H,E,E,O,W,W,O,_,_,_]

        happy = [row[:] for row in base]
        happy[8]  = [O,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,O,_,_,_]
        happy[9]  = [O,W,O,O,O,O,O,W,W,W,W,W,W,O,O,O,O,O,W,W,O,_,_,_]
        happy[10] = [O,W,W,H,H,H,O,W,W,P,P,W,W,O,H,H,H,W,W,W,O,_,_,_]

        eating = [row[:] for row in base]
        eating[11] = [O,W,P,P,F,F,F,F,F,F,F,F,F,F,P,P,W,W,O,_,_,_]
        eating[12] = [_,O,P,P,W,F,F,F,F,F,F,F,F,W,P,P,W,O,_,_,_,_]

        sleep = [row[:] for row in base]
        sleep[8]  = [O,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,O,_,_,_]
        sleep[9]  = [O,W,O,O,O,O,O,W,W,W,W,W,W,O,O,O,O,O,W,W,O,_,_,_]

        dance = [row[:] for row in happy]

        matrix_map = {
            "DRAG": drag, "WALK": walk, "HAPPY": happy,
            "EATING": eating, "SLEEP": sleep, "DANCE": dance, "IDLE": base
        }

        selected = matrix_map.get(self.state, base)
        return [row[::-1] for row in selected] if not self.facing_right else selected

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        matrix = self.get_pixel_matrix()
        pixel_size = 5

        colors = {
            0: C_TRANSPARENT, 1: C_OUTLINE, 2: C_WHITE, 3: C_SHADOW,
            4: C_DARK_PATCH, 5: C_TABBY_LIGHT, 6: C_PINK, 7: C_EYE, 
            8: C_SHINE, 9: C_FOOD
        }

        offset_x = 20
        offset_y = 30 - self.dance_bounce

        # Dibujar Uni
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val != 0:
                    painter.fillRect(
                        offset_x + (x * pixel_size), 
                        offset_y + (y * pixel_size), 
                        pixel_size, pixel_size, 
                        colors.get(val, C_TRANSPARENT)
                    )

        # Dibujar Partículas
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for p in self.particles:
            c = QColor(p.color)
            c.setAlphaF(max(0.0, min(1.0, p.life)))
            painter.setPen(c)
            font = QFont("DejaVu Sans", 9, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(int(p.x), int(p.y), p.symbol)

        # Globo de texto
        if self.speech_text:
            font = QFont("DejaVu Sans", 8, QFont.Weight.Bold)
            painter.setFont(font)

            painter.setBrush(C_BUBBLE_BG)
            painter.setPen(C_OUTLINE)
            painter.drawRoundedRect(15, 5, 150, 24, 8, 8)

            painter.setPen(C_BUBBLE_TEXT)
            painter.drawText(15, 5, 150, 24, Qt.AlignmentFlag.AlignCenter, self.speech_text)

    # --- IA Y ACTUALIZACIONES ---
    def pet_ai_decision(self):
        if self.state in ["DRAG", "SLEEP", "EATING", "HAPPY", "DANCE"]:
            return

        decision = random.choice(["IDLE", "IDLE", "UNI_ACTIONS", "WALK_LEFT", "WALK_RIGHT"])
        if decision == "WALK_LEFT" and not self.is_pinned:
            self.state = "WALK"
            self.facing_right = False
        elif decision == "WALK_RIGHT" and not self.is_pinned:
            self.state = "WALK"
            self.facing_right = True
        elif decision == "UNI_ACTIONS":
            self.state = "IDLE"
            self.show_speech(random.choice([
                ":3", 
                "¿Tienes algo de comer? ✦", 
                "¡Purr~! ~", 
                "(=^･ω･^=)", 
                "¡Mirando fijamente! ★"
            ]))
        else:
            self.state = "IDLE"

    def update_animation(self):
        self.frame = (self.frame + 1) % 2

        # Actualizar partículas
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        # Animación de baile
        if self.state == "DANCE":
            self.dance_bounce = 6 if self.dance_bounce == 0 else 0
            if random.random() < 0.35:
                self.spawn_particles('NOTE', 1)
        else:
            self.dance_bounce = 0

        # Partículas de sueño
        if self.state == "SLEEP" and random.random() < 0.2:
            self.spawn_particles('ZZZ', 1)

        # Movimiento
        if self.state == "WALK" and not self.is_dragging and not self.is_pinned:
            step = 5 if self.facing_right else -5
            new_x = self.x() + step
            
            screen = QApplication.primaryScreen().geometry()
            if 0 <= new_x <= screen.width() - self.width():
                self.move(new_x, self.y())
            else:
                self.facing_right = not self.facing_right

        self.update()

    def update_stats(self):
        if self.state == "SLEEP":
            self.energy = min(100, self.energy + 20)
            if self.energy >= 100:
                self.state = "IDLE"
                self.show_speech("¡Uni despertó! ☼")
        else:
            self.energy = max(0, self.energy - 1)
            self.hunger = max(0, self.hunger - 2)
            self.happiness = max(0, self.happiness - 1)

            if self.hunger < 25 and self.state != "DANCE":
                self.show_speech("Tengo hambre... :3")
            elif self.energy < 15:
                self.state = "SLEEP"
                self.show_speech("Zzz... :3")

    # --- INTERACCIÓN ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_pinned:
                self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self.is_dragging = True
                self.state = "DRAG"
                self.show_speech("¡Ooh~! :3")
            else:
                self.show_speech("¡Uni está fijado! ◆")

        elif event.button() == Qt.MouseButton.RightButton:
            self.show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None and not self.is_pinned:
            self.move(event.globalPosition().toPoint() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        if self.drag_pos is not None and not self.is_pinned:
            self.is_dragging = False
            self.state = "IDLE"
            self.save_position()
            self.drag_pos = None

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        # Estilo QSS para el menú contextual
        menu.setStyleSheet("""
            QMenu {
                background-color: #fff0f3;
                border: 1px solid #231f20;
                color: #4a0e17;
                font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif;
                font-weight: bold;
                padding: 4px;
            }
            QMenu::item {
                padding: 5px 20px 5px 10px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #ff9ebb;
                color: #231f20;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e2e5eb;
                margin: 4px 0px;
            }
        """)

        act_feed = QAction(f"✦ Dar panecillo ({self.hunger}%)", self)
        act_pet = QAction(f"★ Acariciar mofletes ({self.happiness}%)", self)
        act_jump = QAction("▲ Subir a la ventana activa", self)
        act_sleep = QAction("☾ Dormir" if self.state != "SLEEP" else "☼ Despertar", self)
        
        pin_label = "◆ Fijar posición" if not self.is_pinned else "◈ Desbloquear posición"
        act_pin = QAction(pin_label, self)
        
        act_close = QAction("✖ Salir", self)

        act_feed.triggered.connect(self.feed)
        act_pet.triggered.connect(self.pet)
        act_jump.triggered.connect(self.jump_to_active_window)
        act_sleep.triggered.connect(self.toggle_sleep)
        act_pin.triggered.connect(self.toggle_pin)
        act_close.triggered.connect(QApplication.instance().quit)

        menu.addAction(act_feed)
        menu.addAction(act_pet)
        menu.addAction(act_jump)
        menu.addAction(act_sleep)
        menu.addAction(act_pin)
        menu.addSeparator()
        menu.addAction(act_close)
        menu.exec(pos)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.settings.setValue("pinned", self.is_pinned)
        if self.is_pinned:
            self.show_speech("¡Uni fijado aquí! ◆")
        else:
            self.show_speech("¡Puedo caminar! :3")

    def feed(self):
        if self.state == "SLEEP": return
        self.state = "EATING"
        self.hunger = min(100, self.hunger + 35)
        self.spawn_particles('CRUMB', 6)
        self.show_speech("¡Oishii~! ★")
        QTimer.singleShot(2200, lambda: setattr(self, 'state', 'IDLE'))

    def pet(self):
        if self.state == "SLEEP": return
        self.state = "HAPPY"
        self.happiness = min(100, self.happiness + 25)
        self.spawn_particles('HEART', 5)
        self.show_speech("♥ ¡Purrrr~! :3 ♥")
        QTimer.singleShot(2000, lambda: setattr(self, 'state', 'IDLE'))

    def toggle_sleep(self):
        if self.state == "SLEEP":
            self.state = "IDLE"
            self.show_speech("¡Uni despertó!")
        else:
            self.state = "SLEEP"
            self.show_speech("Zzz... :3")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Configurar fuentes del sistema globalmente
    font = app.font()
    font.setFamilies(["DejaVu Sans", "Liberation Sans", "Noto Sans", "Sans-Serif"])
    app.setFont(font)
    
    pet = RealUniTheCat()
    pet.show()
    sys.exit(app.exec())
