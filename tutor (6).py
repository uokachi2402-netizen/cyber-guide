import pygame
import math
import threading
import json
import os
import google.generativeai as genai
from datetime import datetime

# =================================================================
# 1. CẤU HÌNH & DỮ LIỆU
# =================================================================
pygame.init()
info = pygame.display.Info()
W, H = int(info.current_w * 0.9), int(info.current_h * 0.85)
screen = pygame.display.set_mode((W, H), pygame.DOUBLEBUF)
pygame.display.set_caption("CyberGuide OS v2.0 - Total Overhaul")

# Cấu hình API (Vui lòng điền Key của bạn)
API_KEY = "YOUR_API_KEY_HERE"
genai.configure(api_key=API_KEY)

COLORS = {
    "bg": (3, 7, 18), "nav": (15, 23, 42), "accent": (0, 255, 180),
    "card": (20, 30, 50), "border": (51, 65, 85), "text": (241, 245, 249),
    "dim": (120, 135, 160), "danger": (255, 70, 70), "warning": (255, 200, 0)
}

FONT_CACHE = {}
def get_f(size, bold=False):
    key = (size, bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont("Segoe UI, Arial", size, bold=bold)
    return FONT_CACHE[key]

# =================================================================
# 2. HỆ THỐNG QUẢN LÝ DỮ LIỆU (PERSISTENCE)
# =================================================================
class DataManager:
    @staticmethod
    def save_tasks(tasks):
        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False)
    
    @staticmethod
    def load_tasks():
        if os.path.exists("tasks.json"):
            with open("tasks.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return [["08:00", "Khởi động hệ thống", True, 0]] # Giờ, việc, xong, ưu tiên

# =================================================================
# 3. KERNEL ĐIỀU HÀNH
# =================================================================
class CyberKernel:
    def __init__(self):
        self.tab = "HOME"
        self.ai = CyberAI()
        self.sel_method = 0
        self.query = ""
        self.tasks = DataManager.load_tasks()
        
        # Pomodoro Logic
        self.pomo_time = 25 * 60
        self.pomo_active = False
        self.pomo_mode = "WORK" # WORK hoặc BREAK
        
        # Planner Inputs
        self.input_time = ""; self.input_task = ""; self.active_input = "TASK"
        self.ai_scroll_y = 0

        self.methods = [
            {"n": "FEYNMAN", "c": (255, 160, 0), "s": [90, 70, 99, 90, 65], "steps": ["Dạy lại cho trẻ con 6 tuổi.", "Đơn giản hóa thuật ngữ chuyên môn.", "Tìm điểm chưa hiểu và học lại."]},
            {"n": "POMODORO", "c": (255, 60, 110), "s": [85, 99, 60, 40, 95], "steps": ["Chọn 1 việc cần làm.", "Đặt giờ 25 phút.", "Làm tới khi chuông reo."]},
            {"n": "ACTIVE RECALL", "c": (0, 255, 150), "s": [95, 85, 90, 55, 80], "steps": ["Tự kiểm tra thay vì đọc lại.", "Đặt câu hỏi 'Tại sao'?", "Ôn tập ngắt quãng."]}
        ]

    def update_pomo(self):
        if self.pomo_active and self.pomo_time > 0:
            self.pomo_time -= 1/60 
            if self.pomo_time <= 0:
                self.pomo_active = False
                # Có thể thêm âm thanh báo hiệu ở đây

    def add_task(self):
        if self.input_task:
            time_now = self.input_time if self.input_time else datetime.now().strftime("%H:%M")
            self.tasks.append([time_now, self.input_task, False, 0])
            self.tasks.sort(key=lambda x: x[0])
            DataManager.save_tasks(self.tasks)
            self.input_task = ""; self.input_time = ""

    # --- UI DRAWING ---
    def draw_navbar(self, surf):
        pygame.draw.rect(surf, COLORS["nav"], (0, 0, W, 70))
        tabs = ["HOME", "STUDY", "AI", "PLANNER"]
        for i, t in enumerate(tabs):
            tx = i * (W // 4)
            sel = (self.tab == t)
            col = COLORS["accent"] if sel else COLORS["dim"]
            if sel: pygame.draw.rect(surf, COLORS["accent"], (tx+30, 65, (W//4)-60, 3))
            surf.blit(get_f(18, sel).render(f"{i+1}. {t}", True, col), (tx + 50, 22))

    def screen_home(self, surf):
        surf.blit(get_f(60, True).render("CYBERGUIDE v2.0", True, COLORS["text"]), (60, 120))
        t_str = datetime.now().strftime("%A, %d %B %H:%M:%S")
        surf.blit(get_f(22).render(t_str, True, COLORS["accent"]), (65, 190))
        
        # Summary Stats
        done = sum(1 for t in self.tasks if t[2])
        total = len(self.tasks)
        cards = [("TIẾN ĐỘ", f"{done}/{total} Task"), ("AI MEMORY", f"{len(self.ai.history)} Blocks"), ("POMO", self.pomo_mode)]
        for i, (tit, val) in enumerate(cards):
            r = pygame.Rect(60 + i*280, 280, 250, 120)
            pygame.draw.rect(surf, COLORS["card"], r, border_radius=15)
            surf.blit(get_f(14).render(tit, True, COLORS["dim"]), (r.x+20, r.y+20))
            surf.blit(get_f(24, True).render(val, True, COLORS["accent"]), (r.x+20, r.y+55))

    def screen_study(self, surf):
        # LEFT: Methods
        for i, m in enumerate(self.methods):
            m_r = pygame.Rect(50, 120 + i*65, 220, 55)
            sel = (self.sel_method == i)
            pygame.draw.rect(surf, m["c"] if sel else COLORS["card"], m_r, border_radius=12)
            surf.blit(get_f(15, sel).render(m["n"], True, (0,0,0) if sel else COLORS["text"]), (70, 135 + i*65))

        # CENTER: Method Detail
        curr = self.methods[self.sel_method]
        surf.blit(get_f(35, True).render(curr["n"], True, curr["c"]), (300, 120))
        for j, s in enumerate(curr["steps"]):
            surf.blit(get_f(18).render(f"• {s}", True, COLORS["text"]), (300, 200 + j*45))

        # RIGHT: Pomodoro Tool
        p_r = pygame.Rect(W-350, 120, 300, 250)
        pygame.draw.rect(surf, COLORS["card"], p_r, border_radius=20)
        pygame.draw.rect(surf, COLORS["border"], p_r, 1, border_radius=20)
        title = "FOCUS" if self.pomo_mode == "WORK" else "BREAK"
        surf.blit(get_f(20, True).render(title, True, COLORS["accent"]), (p_r.x+105, p_r.y+30))
        
        m, s = divmod(int(self.pomo_time), 60)
        time_text = f"{m:02d}:{s:02d}"
        surf.blit(get_f(60, True).render(time_text, True, COLORS["text"]), (p_r.x+65, p_r.y+70))
        
        # Start/Reset Button
        btn = pygame.Rect(p_r.x+50, p_r.y+170, 200, 45)
        pygame.draw.rect(surf, COLORS["accent"] if not self.pomo_active else COLORS["danger"], btn, border_radius=10)
        txt = "STOP" if self.pomo_active else "START FOCUS"
        surf.blit(get_f(16, True).render(txt, True, (0,0,0)), (btn.centerx-50, btn.centery-10))

    def screen_ai(self, surf):
        chat_r = pygame.Rect(80, 100, W-160, H-300)
        pygame.draw.rect(surf, COLORS["card"], chat_r, border_radius=20)
        
        # Trạng thái AI
        if self.ai.thinking:
            surf.blit(get_f(16).render("Hệ thống đang phân tích...", True, COLORS["accent"]), (100, 115))
        
        # Render hội thoại
        content_y = 140 - self.ai_scroll_y
        for sender, text in self.ai.history[-10:]: # Hiện 10 câu gần nhất
            color = COLORS["accent"] if sender == "user" else COLORS["dim"]
            prefix = "YOU: " if sender == "user" else "CYBER: "
            surf.blit(get_f(15, True).render(prefix, True, color), (110, content_y))
            # Wrap text đơn giản
            words = text.split(' ')
            line = ""
            for w in words:
                if get_f(16).size(line + w)[0] < chat_r.width - 150:
                    line += w + " "
                else:
                    surf.blit(get_f(16).render(line, True, COLORS["text"]), (180, content_y))
                    content_y += 25
                    line = w + " "
            surf.blit(get_f(16).render(line, True, COLORS["text"]), (180, content_y))
            content_y += 40
        
        # Input AI
        in_r = pygame.Rect(80, H-150, W-160, 60)
        pygame.draw.rect(surf, (15, 25, 45), in_r, border_radius=15, width=0)
        pygame.draw.rect(surf, COLORS["accent"], in_r, 1, border_radius=15)
        txt = self.query + ("_" if pygame.time.get_ticks() % 1000 < 500 else "")
        surf.blit(get_f(17).render(txt if txt else "Hỏi trợ lý STEM...", True, COLORS["dim"]), (100, H-132))

    def screen_planner(self, surf):
        for i, (t_v, a_v, d, p) in enumerate(self.tasks):
            r = pygame.Rect(80, 100 + i*60, W-160, 50)
            pygame.draw.rect(surf, COLORS["card"], r, border_radius=10)
            # Checkbox
            ck = pygame.Rect(r.x+15, r.y+12, 25, 25)
            pygame.draw.rect(surf, COLORS["accent"], ck, 2, border_radius=5)
            if d: pygame.draw.rect(surf, COLORS["accent"], ck.inflate(-10,-10))
            # Text
            col = COLORS["dim"] if d else COLORS["text"]
            surf.blit(get_f(16).render(f"{t_v}", True, COLORS["accent"]), (r.x+60, r.y+13))
            surf.blit(get_f(16).render(a_v, True, col), (r.x+140, r.y+13))
            # Delete btn
            del_b = pygame.Rect(r.right-40, r.y+12, 25, 25)
            surf.blit(get_f(18, True).render("×", True, COLORS["danger"]), (del_b.x+5, del_b.y-2))

        # Bottom Input
        in_v = pygame.Rect(80, H-100, W-160, 50)
        pygame.draw.rect(surf, (10, 20, 30), in_v, border_radius=10)
        surf.blit(get_f(16).render(f"Task: {self.input_task}", True, COLORS["text"]), (100, H-85))

class CyberAI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat = self.model.start_chat(history=[])
        self.history = [("model", "CyberGuide OS đã sẵn sàng. Bạn muốn học gì hôm nay?")]
        self.thinking = False

    def ask(self, prompt):
        if not prompt or self.thinking: return
        self.thinking = True
        self.history.append(("user", prompt))
        threading.Thread(target=self._run, args=(prompt,), daemon=True).start()

    def _run(self, prompt):
        try:
            res = self.chat.send_message(f"Học sinh lớp 7 hỏi: {prompt}. Trả lời ngắn, có dùng icon.")
            self.history.append(("model", res.text))
        except:
            self.history.append(("model", "Lỗi kết nối. Kiểm tra API Key/Internet!"))
        self.thinking = False

# =================================================================
# 4. MAIN LOOP
# =================================================================
kernel = CyberKernel()
clock = pygame.time.Clock()

while True:
    screen.fill(COLORS["bg"])
    kernel.update_pomo()
    kernel.draw_navbar(screen)

    if kernel.tab == "HOME": kernel.screen_home(screen)
    elif kernel.tab == "STUDY": kernel.screen_study(screen)
    elif kernel.tab == "AI": kernel.screen_ai(screen)
    elif kernel.tab == "PLANNER": kernel.screen_planner(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            DataManager.save_tasks(kernel.tasks)
            pygame.quit(); exit()
        
        if event.type == pygame.KEYDOWN:
            # Phím tắt chuyển Tab
            if event.key == pygame.K_1: kernel.tab = "HOME"
            if event.key == pygame.K_2: kernel.tab = "STUDY"
            if event.key == pygame.K_3: kernel.tab = "AI"
            if event.key == pygame.K_4: kernel.tab = "PLANNER"
            
            # Input Logic
            if kernel.tab == "AI":
                if event.key == pygame.K_BACKSPACE: kernel.query = kernel.query[:-1]
                elif event.key == pygame.K_RETURN: 
                    kernel.ai.ask(kernel.query); kernel.query = ""
                else: kernel.query += event.unicode
            elif kernel.tab == "PLANNER":
                if event.key == pygame.K_BACKSPACE: kernel.input_task = kernel.input_task[:-1]
                elif event.key == pygame.K_RETURN: kernel.add_task()
                else: kernel.input_task += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Click chuyển Tab bằng chuột
            if event.pos[1] < 70:
                idx = event.pos[0] // (W // 4)
                kernel.tab = ["HOME", "STUDY", "AI", "PLANNER"][idx]
            
            # Pomo Button
            if kernel.tab == "STUDY":
                if pygame.Rect(W-300, 290, 200, 45).collidepoint(event.pos):
                    kernel.pomo_active = not kernel.pomo_active
            
            # Planner Checkbox/Delete
            if kernel.tab == "PLANNER":
                for i in range(len(kernel.tasks)):
                    if pygame.Rect(95, 112+i*60, 25, 25).collidepoint(event.pos):
                        kernel.tasks[i][2] = not kernel.tasks[i][2]
                    if pygame.Rect(W-120, 112+i*60, 25, 25).collidepoint(event.pos):
                        kernel.tasks.pop(i); break

    pygame.display.flip()
    clock.tick(60)