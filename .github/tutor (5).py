import pygame
import math
import time
import threading
import random
import sys
import google.generativeai as genai

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & AI
# ==========================================
API_KEY = "AIzaSyBb0pyBN3JrRAWI9bExFo1mvqdvp3JeNmI" 
try:
    genai.configure(api_key=API_KEY.strip())
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction="Bạn là CyberGuide, trợ lý học tập lớp 7 tại Hải Phòng. Trả lời cực kỳ ngắn gọn, dùng emoji, thân thiện."
    )
except Exception as e:
    print("Lỗi khởi tạo AI:", e)

pygame.init()
info = pygame.display.Info()
# Tối ưu hóa kích thước màn hình
W, H = int(info.current_w * 0.9), int(info.current_h * 0.9)
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE | pygame.DOUBLEBUF)
pygame.display.set_caption("CyberGuide OS v3.5 - Ultimate STEM Project")

def get_f(size, bold=False):
    return pygame.font.SysFont("segoe ui, tahoma, arial", size, bold=bold)

# ==========================================
# 2. GIAO DIỆN, THEME & HIỆU ỨNG HẠT
# ==========================================
IS_LIGHT_MODE = False
def get_theme():
    if IS_LIGHT_MODE:
        return {"bg": (240, 245, 250), "nav": (210, 220, 235), "card": (255, 255, 255), 
                "text": (30, 40, 60), "accent": (0, 110, 200), "p": (0, 110, 200, 40), 
                "danger": (244, 63, 94), "success": (34, 197, 94), "dim": (120, 130, 150)}
    return {"bg": (5, 5, 20), "nav": (15, 20, 45), "card": (20, 30, 60), 
            "text": (240, 250, 255), "accent": (0, 255, 200), "p": (0, 255, 200, 40), 
            "danger": (255, 80, 100), "success": (50, 220, 100), "dim": (100, 116, 139)}

class NanoParticle:
    def __init__(self):
        self.x, self.y = random.randint(0, W), random.randint(0, H)
        self.vx, self.vy = random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)
        self.size = random.uniform(1, 3)
    def update(self):
        self.x += self.vx; self.y += self.vy
        if self.x < 0 or self.x > W: self.vx *= -1
        if self.y < 0 or self.y > H: self.vy *= -1
    def draw(self, surf, color):
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), int(self.size))

# ==========================================
# 3. KERNEL XỬ LÝ LỊCH TRÌNH & VA CHẠM
# ==========================================
class CyberKernel:
    def __init__(self):
        self.tasks = []
        self.sleep_night = "22:30-06:00"
        self.sleep_nap = "12:00-13:00"
        self.error_msg = ""
        self.alert_timer = 0
        
    def time_to_min(self, t_str):
        try:
            h, m = map(int, t_str.strip().split(":"))
            return h * 60 + m
        except: return -1

    def calc_h(self, r_str):
        try:
            s, e = r_str.split("-")
            d = (self.time_to_min(e) - self.time_to_min(s)) / 60
            return d if d > 0 else d + 24
        except: return 0

    def get_total_sleep(self):
        return self.calc_h(self.sleep_night) + self.calc_h(self.sleep_nap)

    def check_collision(self, new_range):
        try:
            if "-" in new_range: ns_str, ne_str = new_range.split("-")
            else: ns_str = new_range; ne_str = f"{(int(ns_str.split(':')[0])+1)%24:02d}:{ns_str.split(':')[1]}"
            ns, ne = self.time_to_min(ns_str), self.time_to_min(ne_str)
            if ns == -1 or ne == -1: return "Định dạng sai (HH:MM)"
            if ne <= ns: ne += 1440 

            for s_label, s_range in [("Ngủ đêm", self.sleep_night), ("Ngủ trưa", self.sleep_nap)]:
                ss_str, se_str = s_range.split("-")
                ss, se = self.time_to_min(ss_str), self.time_to_min(se_str)
                if se <= ss: se += 1440
                if max(ns, ss) < min(ne, se): return f"Trùng lịch {s_label}"
            
            for t in self.tasks:
                ts, te = self.time_to_min(t["time"].split("-")[0]), self.time_to_min(t["time"].split("-")[1])
                if te <= ts: te += 1440
                if max(ns, ts) < min(ne, te): return f"Trùng lịch: {t['content']}"
            return None
        except: return "Lỗi thời gian"

    def add_task(self, raw):
        if not raw.strip(): return
        parts = raw.split(" ", 1)
        if len(parts) < 2: self.show_err("Nhập: HH:MM Nội dung"); return
        col = self.check_collision(parts[0])
        if col: self.show_err(col); return
        t_str = parts[0]
        if "-" not in t_str: t_str = f"{t_str}-{(int(t_str.split(':')[0])+1)%24:02d}:{t_str.split(':')[1]}"
        self.tasks.append({"time": t_str, "content": parts[1]})
        self.tasks.sort(key=lambda x: self.time_to_min(x["time"].split("-")[0]))

    def show_err(self, msg):
        self.error_msg = msg
        self.alert_timer = 180 

# ==========================================
# 4. HÀM VẼ UI NÂNG CAO (Radar, Chat Wrap)
# ==========================================
def draw_text_wrapped(surf, text, color, rect, font):
    words = text.split(' '); lines, curr = [], ""
    for w in words:
        if font.size(curr + w)[0] < rect.width: curr += w + " "
        else: lines.append(curr); curr = w + " "
    lines.append(curr)
    for i, l in enumerate(lines):
        txt_s = font.render(l, True, color)
        surf.blit(txt_s, (rect.x, rect.y + i*28))
    return len(lines)*28

def draw_radar(surf, center, stats, color, labels):
    num_vars = len(labels); radius = 100
    for r in [40, 70, 100]:
        grid = [(center[0]+r*math.cos(-math.pi/2+i*2*math.pi/num_vars), center[1]+r*math.sin(-math.pi/2+i*2*math.pi/num_vars)) for i in range(num_vars)]
        pygame.draw.polygon(surf, (150, 150, 150, 80) if IS_LIGHT_MODE else (50, 60, 90), grid, 1)
    pts = []
    for i in range(num_vars):
        ang = -math.pi/2+i*2*math.pi/num_vars
        val_r = (stats[i]/100)*radius
        pts.append((center[0]+val_r*math.cos(ang), center[1]+val_r*math.sin(ang)))
        txt = get_f(12, True).render(labels[i], True, color)
        surf.blit(txt, (center[0]+(radius+35)*math.cos(ang)-txt.get_width()//2, center[1]+(radius+25)*math.sin(ang)-10))
    if len(pts) > 2:
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(ov, (*color, 80), pts); surf.blit(ov, (0,0))
        pygame.draw.polygon(surf, color, pts, 3)

def ask_ai_thread(prompt_text):
    global ai_is_thinking, chat_scroll
    try:
        response = model.generate_content(prompt_text)
        txt = response.text.strip() if response and response.text else "AI đang bối rối..."
        chat_log.append({"s": "AI", "t": txt})
    except:
        chat_log.append({"s": "AI", "t": "Lỗi kết nối AI! 🔌"})
    ai_is_thinking = False

# ==========================================
# 5. KHỞI TẠO DỮ LIỆU & PHƯƠNG PHÁP
# ==========================================
METHODS = [
    {"name": "ACTIVE RECALL", "color": (255, 40, 80), "radar": [99, 85, 95, 45, 50], "steps": ["Đóng sách lại ngay.", "Tự đặt câu hỏi trong đầu.", "Truy xuất thông tin mà không xem tài liệu."]},
    {"name": "FEYNMAN", "color": (255, 0, 150), "radar": [97, 60, 98, 85, 45], "steps": ["Chọn 1 chủ đề khó.", "Giảng lại cho một đứa trẻ 5 tuổi.", "Lấp đầy lỗ hổng kiến thức qua tài liệu."]},
    {"name": "POMODORO", "color": (0, 255, 150), "radar": [70, 95, 60, 40, 90], "steps": ["Làm việc tập trung 25 phút.", "Nghỉ ngơi hoàn toàn 5 phút.", "Lặp lại chu kỳ 4 lần."]}
]

kernel = CyberKernel()
particles = [NanoParticle() for _ in range(50)]
current_tab = "TRANG CHỦ"
tabs = ["TRANG CHỦ", "LỊCH TRÌNH", "PHƯƠNG PHÁP", "TRUNG TÂM AI"]

chat_log = [{"s": "AI", "t": "Chào bạn! Mình là CyberGuide. Hãy bắt đầu bằng việc thiết lập giờ ngủ nhé! 🚀"}]
ai_is_thinking, chat_scroll, chat_h = False, 0, 0
user_in, in_act = "", False
sel_meth = 0; anim_stats = [0.0] * 5

is_setting_up, setup_step, setup_input = True, 0, ""
theme_btn = pygame.Rect(W - 80, 15, 60, 50)
clock = pygame.time.Clock(); run = True
pygame.key.start_text_input()

# ==========================================
# 6. VÒNG LẶP CHÍNH (MAIN LOOP)
# ==========================================
while run:
    theme = get_theme(); screen.fill(theme["bg"])
    for p in particles: 
        p.update(); p.draw(screen, theme["p"])
    
    # --- THANH NAVIGATION ---
    pygame.draw.rect(screen, (*theme["nav"], 240), (0,0,W,80))
    tw = W // (len(tabs) + 1)
    for i, name in enumerate(tabs):
        r = pygame.Rect(i*tw, 0, tw, 80)
        is_sel = (current_tab == name)
        if is_sel: pygame.draw.rect(screen, theme["accent"], (r.x, 76, r.width, 4))
        txt = get_f(16, is_sel).render(name, True, theme["accent"] if is_sel else theme["dim"])
        screen.blit(txt, (r.centerx-txt.get_width()//2, 30))
    pygame.draw.circle(screen, (255, 200, 0) if IS_LIGHT_MODE else (100, 255, 200), theme_btn.center, 15)

    # --- NỘI DUNG TỪNG TAB ---
    if current_tab == "TRANG CHỦ":
        screen.blit(get_f(70, True).render("CYBERGUIDE OS", True, theme["accent"]), (70, 150))
        # Card ngủ
        box_n = pygame.Rect(70, 280, 350, 180); pygame.draw.rect(screen, theme["card"], box_n, border_radius=25)
        screen.blit(get_f(20, True).render("NGHỈ NGƠI", True, theme["dim"]), (box_n.x+30, box_n.y+25))
        screen.blit(get_f(18).render(f"🌙 Đêm: {kernel.sleep_night}", True, theme["text"]), (box_n.x+30, box_n.y+65))
        screen.blit(get_f(18).render(f"☀️ Trưa: {kernel.sleep_nap}", True, theme["text"]), (box_n.x+30, box_n.y+95))
        sh = kernel.get_total_sleep()
        screen.blit(get_f(35, True).render(f"{sh:.1f}H", True, theme["success"] if sh>=8 else theme["danger"]), (box_n.x+30, box_n.y+130))
        # Card nhiệm vụ
        box_t = pygame.Rect(450, 280, 350, 180); pygame.draw.rect(screen, theme["card"], box_t, border_radius=25)
        screen.blit(get_f(20, True).render("NHIỆM VỤ", True, theme["dim"]), (box_t.x+30, box_t.y+25))
        screen.blit(get_f(60, True).render(str(len(kernel.tasks)), True, theme["accent"]), (box_t.x+30, box_t.y+70))

    elif current_tab == "LỊCH TRÌNH":
        # Header cố định
        pygame.draw.rect(screen, theme["nav"], (60, 100, W-120, 60), border_radius=15)
        screen.blit(get_f(18, True).render(f"CHẾ ĐỘ NGỦ TÁCH BIỆT ĐÃ KÍCH HOẠT", True, theme["accent"]), (90, 118))
        
        for i, t in enumerate(kernel.tasks):
            ry = 180 + i*65
            if ry > H - 180: break
            rect = pygame.Rect(60, ry, W-120, 55); pygame.draw.rect(screen, theme["card"], rect, border_radius=15)
            pygame.draw.rect(screen, theme["accent"], (rect.x, rect.y, 8, 55), border_top_left_radius=15, border_bottom_left_radius=15)
            screen.blit(get_f(22, True).render(t["time"], True, theme["accent"]), (90, ry+12))
            screen.blit(get_f(20).render(t["content"], True, theme["text"]), (280, ry+12))
            # Nút xóa
            del_r = pygame.Rect(W-110, ry+10, 35, 35); pygame.draw.rect(screen, (200, 50, 50), del_r, border_radius=10)
            screen.blit(get_f(18, True).render("X", True, (255,255,255)), (del_r.x+10, del_r.y+5))
            
        # Input Bar
        in_r = pygame.Rect(60, H-100, W-120, 70); pygame.draw.rect(screen, theme["card"], in_r, border_radius=20)
        border_c = theme["danger"] if kernel.alert_timer > 0 else (theme["accent"] if in_act else theme["dim"])
        pygame.draw.rect(screen, border_c, in_r, 2, border_radius=20)
        disp = kernel.error_msg if kernel.alert_timer > 0 else (user_in + ("|" if in_act and time.time()%1>0.5 else ""))
        if not user_in and not in_act and kernel.alert_timer == 0: disp = "Nhập: HH:MM Công việc (VD: 15:30 Học Toán)..."
        screen.blit(get_f(20).render(disp, True, theme["danger"] if kernel.alert_timer>0 else theme["text"]), (90, H-78))
        if kernel.alert_timer > 0: kernel.alert_timer -= 1

    elif current_tab == "PHƯƠNG PHÁP":
        for i, m in enumerate(METHODS):
            ry = 120 + i*70; is_s = (i == sel_meth)
            btn = pygame.Rect(60, ry, 300, 60); pygame.draw.rect(screen, m['color'] if is_s else theme["card"], btn, border_radius=15)
            screen.blit(get_f(18, is_s).render(m['name'], True, (255,255,255) if is_s else theme["text"]), (90, ry+18))
        # Info Panel
        panel = pygame.Rect(400, 120, W-460, H-220); pygame.draw.rect(screen, theme["card"], panel, border_radius=30)
        screen.blit(get_f(35, True).render(METHODS[sel_meth]['name'], True, METHODS[sel_meth]['color']), (panel.x+50, panel.y+50))
        for i, s in enumerate(METHODS[sel_meth]['steps']):
            screen.blit(get_f(20).render(f"➤ {s}", True, theme["text"]), (panel.x+55, panel.y+130+i*50))
        # Radar
        for i in range(5): anim_stats[i] += (METHODS[sel_meth]['radar'][i] - anim_stats[i]) * 0.1
        draw_radar(screen, (panel.x + panel.width - 220, panel.y + 220), anim_stats, METHODS[sel_meth]['color'], ["H.Quả", "Tốc Độ", "Độ Sâu", "Sáng Tạo", "Bền Vững"])

    elif current_tab == "TRUNG TÂM AI":
        chat_box = pygame.Rect(60, 100, W-120, H-230); pygame.draw.rect(screen, theme["card"], chat_box, border_radius=25)
        c_surf = pygame.Surface((chat_box.width, 5000), pygame.SRCALPHA); cy = 30
        for log in chat_log:
            is_ai = log['s'] == "AI"
            pygame.draw.rect(c_surf, theme["nav"] if is_ai else theme["accent"], (20, cy, chat_box.width-40, 1), 1) # Separator
            screen_name = "🤖 CYBERGUIDE" if is_ai else "👤 BẠN"
            c_surf.blit(get_f(14, True).render(screen_name, True, theme["accent"] if is_ai else theme["dim"]), (40, cy))
            cy += 30
            cy += draw_text_wrapped(c_surf, log['t'], theme["text"], pygame.Rect(40, cy, chat_box.width-80, 4000), get_f(20)) + 35
            chat_h = cy
        screen.blit(c_surf, (chat_box.x, chat_box.y), (0, chat_scroll, chat_box.width, chat_box.height))
        # Input
        in_r = pygame.Rect(60, H-100, W-120, 70); pygame.draw.rect(screen, theme["card"], in_r, border_radius=20)
        pygame.draw.rect(screen, theme["accent"] if in_act else theme["dim"], in_r, 2, border_radius=20)
        disp_ai = "Đang kết nối não bộ Cyber..." if ai_is_thinking else (user_in + ("|" if in_act and time.time()%1>0.5 else ""))
        screen.blit(get_f(20).render(disp_ai, True, theme["text"]), (90, H-78))

    # --- LỚP PHỦ THIẾT LẬP (SETUP) ---
    if is_setting_up:
        ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 230)); screen.blit(ov, (0,0))
        box = pygame.Rect(W//2-300, H//2-180, 600, 360); pygame.draw.rect(screen, theme["card"], box, border_radius=35)
        pygame.draw.rect(screen, theme["accent"], box, 3, border_radius=35)
        tit = "1. GIỜ NGỦ ĐÊM" if setup_step == 0 else "2. GIỜ NGỦ TRƯA"
        screen.blit(get_f(30, True).render(tit, True, theme["accent"]), (box.x+50, box.y+50))
        screen.blit(get_f(18).render("Định dạng bắt buộc: HH:MM-HH:MM", True, theme["dim"]), (box.x+50, box.y+105))
        in_b = pygame.Rect(box.x+50, box.y+150, 500, 70); pygame.draw.rect(screen, theme["nav"], in_b, border_radius=20)
        screen.blit(get_f(28).render(setup_input + ("|" if time.time()%1>0.5 else ""), True, theme["accent"]), (in_b.x+30, in_b.y+15))
        screen.blit(get_f(16, True).render("NHẤN ENTER ĐỂ LƯU & TIẾP TỤC", True, theme["dim"]), (box.x+50, box.y+280))

    # --- HỆ THỐNG XỬ LÝ SỰ KIỆN (MẠNH MẼ NHẤT) ---
    for e in pygame.event.get():
        if e.type == pygame.QUIT: run = False
        
        if e.type == pygame.MOUSEBUTTONDOWN:
            if not is_setting_up:
                if theme_btn.collidepoint(e.pos): IS_LIGHT_MODE = not IS_LIGHT_MODE
                for i in range(len(tabs)):
                    if pygame.Rect(i*tw, 0, tw, 80).collidepoint(e.pos):
                        current_tab = tabs[i]; user_in = ""; chat_scroll = 0
                # Focus input
                in_act = True if pygame.Rect(60, H-100, W-120, 70).collidepoint(e.pos) else False
                # Xóa task
                if current_tab == "LỊCH TRÌNH":
                    for i in range(len(kernel.tasks)):
                        if pygame.Rect(W-110, 180+i*65+10, 35, 35).collidepoint(e.pos):
                            kernel.tasks.pop(i); break
                if current_tab == "PHƯƠNG PHÁP":
                    for i in range(len(METHODS)):
                        if pygame.Rect(60, 120+i*70, 300, 60).collidepoint(e.pos): sel_meth = i
                if current_tab == "TRUNG TÂM AI":
                    if e.button == 4: chat_scroll = max(0, chat_scroll - 60)
                    if e.button == 5: chat_scroll = min(chat_h - 400, chat_scroll + 60)

        if e.type == pygame.KEYDOWN:
            if is_setting_up:
                if e.key == pygame.K_BACKSPACE: setup_input = setup_input[:-1]
                elif e.key == pygame.K_RETURN and "-" in setup_input:
                    if setup_step == 0: kernel.sleep_night = setup_input; setup_input = ""; setup_step = 1
                    else: kernel.sleep_nap = setup_input; is_setting_up = False
            elif in_act:
                if e.key == pygame.K_BACKSPACE: user_in = user_in[:-1]
                elif e.key == pygame.K_RETURN and user_in.strip() != "":
                    if current_tab == "LỊCH TRÌNH":
                        kernel.add_task(user_in)
                        if kernel.alert_timer == 0: user_in = ""
                    elif current_tab == "TRUNG TÂM AI" and not ai_is_thinking:
                        chat_log.append({"s": "ME", "t": user_in}); ai_is_thinking = True
                        threading.Thread(target=ask_ai_thread, args=(user_in,)).start(); user_in = ""

        if e.type == pygame.TEXTINPUT:
            if is_setting_up: setup_input += e.text
            elif in_act and not ai_is_thinking: user_in += e.text

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
sys.exit()