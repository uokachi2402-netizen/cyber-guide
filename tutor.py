import pygame
import math
import time
import threading
import random
import google.generativeai as genai

# ==========================================
# CẤU HÌNH AI
# ==========================================
API_KEY = "AIzaSyAwBJojv6_Ru1Yy0wpsT0ie15WTDwOto2M"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# ==========================================
# KHỞI TẠO HỆ THỐNG
# ==========================================
pygame.init()
info = pygame.display.Info()
W, H = int(info.current_w * 0.95), int(info.current_h * 0.9)
screen = pygame.display.set_mode((W, H), pygame.DOUBLEBUF | pygame.HWSURFACE)
pygame.display.set_caption("CyberGuide OS v13 - Fixed Scroll")

def get_f(size, bold=True):
    return pygame.font.SysFont("tahoma, segoe ui, arial", size, bold=bold)

DARK_BG, ACCENT, TEXT_WHITE = (5, 5, 20), (0, 255, 200), (240, 250, 255)

# DANH SÁCH PHƯƠNG PHÁP
METHODS = [
    {"name": "1. ACTIVE RECALL", "color": (255, 40, 80), "radar": [99, 85, 95, 45, 40], "steps": ["Đóng sách lại.", "Tự đặt câu hỏi.", "Truy xuất thông tin ngay."]},
    {"name": "2. FEYNMAN", "color": (255, 0, 150), "radar": [97, 60, 98, 85, 45], "steps": ["Chọn chủ đề khó.", "Giảng lại dễ hiểu.", "Đơn giản hóa nội dung."]},
    {"name": "3. SPACED REPETITION", "color": (255, 0, 255), "radar": [95, 45, 92, 35, 65], "steps": ["Ôn lại 1-7-30 ngày.", "Giãn cách thời gian.", "Dùng Flashcards."]},
    {"name": "4. BLURTING", "color": (200, 50, 255), "radar": [90, 80, 85, 50, 55], "steps": ["Đọc nhanh tài liệu.", "Ghi hết ra giấy.", "So sánh phần thiếu."]},
    {"name": "5. INTERLEAVING", "color": (100, 100, 255), "radar": [88, 70, 80, 60, 50], "steps": ["Học xen kẽ môn.", "Không học 1 môn lâu.", "Phân biệt dạng bài Fortran."]}
]

# --- HÀM VẼ RADAR SẮC NÉT & % ---
def draw_radar(surf, center, stats, color, labels):
    num_vars = len(labels)
    radius = 110
    pts_data = []

    for r in [40, 80, 110]:
        grid_pts = []
        for i in range(num_vars):
            angle = -math.pi/2 + i * (2 * math.pi / num_vars)
            grid_pts.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
        pygame.draw.polygon(surf, (35, 45, 80), grid_pts, 1)

    for i in range(num_vars):
        angle = -math.pi/2 + i * (2 * math.pi / num_vars)
        val_r = (stats[i] / 100) * radius
        dx = center[0] + val_r * math.cos(angle)
        dy = center[1] + val_r * math.sin(angle)
        pts_data.append((dx, dy))

        lx = center[0] + (radius + 45) * math.cos(angle)
        ly = center[1] + (radius + 25) * math.sin(angle)
        txt_n = get_f(11).render(labels[i], True, (150, 180, 200))
        txt_p = get_f(13, True).render(f"{stats[i]}%", True, color)
        surf.blit(txt_n, (lx - txt_n.get_width()//2, ly - 15))
        surf.blit(txt_p, (lx - txt_p.get_width()//2, ly + 5))

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.polygon(overlay, (*color, 90), pts_data)
    surf.blit(overlay, (0, 0))
    pygame.draw.polygon(surf, color, pts_data, 3)
    for p in pts_data:
        pygame.draw.circle(surf, (255, 255, 255), (int(p[0]), int(p[1])), 4)

# HỆ THỐNG HẠT NANO
class NanoParticle:
    def __init__(self):
        self.x, self.y = random.randint(0, W), random.randint(0, H)
        self.vx, self.vy = random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6)
    def update(self):
        self.x += self.vx; self.y += self.vy
        if self.x < 0 or self.x > W: self.vx *= -1
        if self.y < 0 or self.y > H: self.vy *= -1
    def draw(self, surf):
        pygame.draw.circle(surf, (0, 255, 200, 100), (int(self.x), int(self.y)), 2)

particles = [NanoParticle() for _ in range(60)]

# HÀM AI THREAD
def ask_ai_thread(p):
    global ai_is_thinking
    try:
        r = model.generate_content(f"Bạn là CyberGuide trợ lý lớp 7. Trả lời ngắn: {p}")
        chat_log.append({"s": "AI", "t": r.text.strip()})
    except: chat_log.append({"s": "AI", "t": "Lỗi AI."})
    ai_is_thinking = False

def draw_text(surface, text, color, rect, font):
    words = text.split(' '); lines, curr = [], ""
    for w in words:
        if font.size(curr + w)[0] < rect.width: curr += w + " "
        else: lines.append(curr); curr = w + " "
    lines.append(curr)
    for i, l in enumerate(lines):
        surface.blit(font.render(l, True, color), (rect.x, rect.y + i*25))
    return len(lines)*25

# TRẠNG THÁI
current_tab = "TRANG CHỦ"
sel_meth = 0
chat_log = [{"s": "AI", "t": "Chào bạn! Hệ thống CyberGuide OS v13 đã sẵn sàng hỗ trợ học tập."}]
ai_is_thinking, chat_scroll, chat_h = False, 0, 0
user_in, in_act = "", False

clock = pygame.time.Clock(); run = True
pygame.key.start_text_input()
p_surf = pygame.Surface((W, H), pygame.SRCALPHA)

# --- VÒNG LẶP CHÍNH ---
while run:
    screen.fill(DARK_BG)
    p_surf.fill((0,0,0,0))
    for p in particles: p.update(); p.draw(p_surf)
    for i, p1 in enumerate(particles):
        for p2 in particles[i+1:]:
            d = math.hypot(p1.x-p2.x, p1.y-p2.y)
            if d < 80: pygame.draw.line(p_surf, (0,255,200,int(50*(1-d/80))), (p1.x,p1.y), (p2.x,p2.y), 1)
    screen.blit(p_surf, (0,0))

    # NAV BAR
    pygame.draw.rect(screen, (15,20,45,220), (0,0,W,80))
    tabs = ["TRANG CHỦ", "PHƯƠNG PHÁP", "TRUNG TÂM AI"]
    tab_rects = []
    for i, name in enumerate(tabs):
        r = pygame.Rect(i*(W//3), 0, W//3, 80)
        tab_rects.append(r)
        if current_tab == name: pygame.draw.rect(screen, ACCENT, r)
        txt = get_f(18, True).render(name, True, (0,0,0) if current_tab == name else (150,160,180))
        screen.blit(txt, (r.centerx-txt.get_width()//2, 25))

    # TRANG CHỦ
    if current_tab == "TRANG CHỦ":
        title_font = get_f(60, True)
        title_surf = title_font.render("CYBERGUIDE OS", True, ACCENT)
        screen.blit(title_font.render("CYBERGUIDE OS", True, (0, 100, 80)), (W//2 - title_surf.get_width()//2 + 4, 114))
        screen.blit(title_surf, (W//2 - title_surf.get_width()//2, 110))
        screen.blit(get_f(18).render("The Future of STEM Learning - Version 13.0", True, TEXT_WHITE), (W//2 - 170, 185))

        card_ai = pygame.Rect(W//2 - 360, 240, 340, 180)
        card_meth = pygame.Rect(W//2 + 20, 240, 340, 180)
        pygame.draw.rect(screen, (20, 30, 60, 200), card_ai, border_radius=15); pygame.draw.rect(screen, ACCENT, card_ai, 2, border_radius=15)
        screen.blit(get_f(22, True).render("TRUNG TÂM AI", True, ACCENT), (card_ai.x+30, card_ai.y+30))
        screen.blit(get_f(14).render("Hỏi đáp kiến thức lớp 7,", True, TEXT_WHITE), (card_ai.x+30, card_ai.y+70))
        
        pygame.draw.rect(screen, (20, 30, 60, 200), card_meth, border_radius=15); pygame.draw.rect(screen, (255, 50, 150), card_meth, 2, border_radius=15)
        screen.blit(get_f(22, True).render("PHƯƠNG PHÁP", True, (255, 50, 150)), (card_meth.x+30, card_meth.y+30))
        screen.blit(get_f(14).render("Khám phá Top 10 cách học", True, TEXT_WHITE), (card_meth.x+30, card_meth.y+70))

        guide_r = pygame.Rect(W//2 - 360, 450, 720, 150)
        pygame.draw.rect(screen, (10, 15, 30, 150), guide_r, border_radius=20); pygame.draw.rect(screen, (100, 100, 100), guide_r, 1, border_radius=20)
        screen.blit(get_f(18, True).render("HƯỚNG DẪN SỬ DỤNG NHANH:", True, (200, 200, 200)), (guide_r.x+30, guide_r.y+20))
        guides = ["• Chạm vào các thanh menu phía trên để chuyển đổi tính năng.", "• Tab PHƯƠNG PHÁP: Chọn danh sách bên trái để xem biểu đồ Radar.", "• Tab TRUNG TÂM AI: Gõ câu hỏi vào ô dưới cùng và nhấn ENTER."]
        for i, g in enumerate(guides): screen.blit(get_f(13).render(g, True, (180, 180, 180)), (guide_r.x+35, guide_r.y+55 + i*22))

    elif current_tab == "PHƯƠNG PHÁP":
        pygame.draw.rect(screen, (10,15,35,180), (15, 95, 320, H-110), border_radius=15)
        for i, meth in enumerate(METHODS):
            ry, is_s = 105 + i*58, (i == sel_meth)
            pygame.draw.rect(screen, meth['color'] if is_s else (30,35,60,180), (25, ry, 300, 52), border_radius=10)
            screen.blit(get_f(12, is_s).render(meth['name'], True, (0,0,0) if is_s else (220,220,220)), (40, ry+16))
        
        draw_radar(screen, (W - 220, 300), METHODS[sel_meth]['radar'], METHODS[sel_meth]['color'], ["Hiệu quả", "Tốc độ", "Độ sâu", "Sáng tạo", "Bền vững"])
        
        step_p = pygame.Rect(350, 95, W-370-400, H-110)
        pygame.draw.rect(screen, (10,15,35,180), step_p, border_radius=20)
        for i, st in enumerate(METHODS[sel_meth]['steps']):
            draw_text(screen, f"• {st}", TEXT_WHITE, pygame.Rect(step_p.x+30, step_p.y+60+i*110, step_p.width-60, 100), get_f(16))

    elif current_tab == "TRUNG TÂM AI":
        chat_c = pygame.Rect(30, 110, W-100, H-250)
        pygame.draw.rect(screen, (10,15,35,200), chat_c, border_radius=20)
        c_surf = pygame.Surface((chat_c.width, 5000), pygame.SRCALPHA); cy = 20
        for log in chat_log:
            clr = ACCENT if log['s'] == "AI" else TEXT_WHITE
            c_surf.blit(get_f(13, True).render(f"{log['s']}:", True, clr), (15, cy))
            h = draw_text(c_surf, log['t'], clr, pygame.Rect(50, cy+20, chat_c.width-80, 4000), get_f(14, False))
            cy += h + 40
            chat_h = cy
        
        # FIX: chat_scroll giờ được blit chính xác theo hướng lăn chuột
        screen.blit(c_surf, (chat_c.x, chat_c.y), (0, chat_scroll, chat_c.width, chat_c.height))
        
        in_r = pygame.Rect(40, H-95, W-100, 65)
        pygame.draw.rect(screen, (5,10,25), in_r, border_radius=12); pygame.draw.rect(screen, ACCENT if in_act else (60,60,80), in_r, 2, border_radius=12)
        screen.blit(get_f(16).render(user_in + ("|" if in_act and time.time()%1>0.5 else ""), True, TEXT_WHITE), (in_r.x+20, in_r.y+20))

    for e in pygame.event.get():
        if e.type == pygame.QUIT: run = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            for i, r in enumerate(tab_rects):
                if r.collidepoint(e.pos): current_tab = tabs[i]
            if current_tab == "TRANG CHỦ":
                if pygame.Rect(W//2 - 360, 240, 340, 180).collidepoint(e.pos): current_tab = "TRUNG TÂM AI"
                if pygame.Rect(W//2 + 20, 240, 340, 180).collidepoint(e.pos): current_tab = "PHƯƠNG PHÁP"
            if current_tab == "PHƯƠNG PHÁP":
                for i in range(len(METHODS)):
                    if pygame.Rect(25, 105+i*58, 300, 52).collidepoint(e.pos): sel_meth = i
            in_act = True if pygame.Rect(40, H-95, W-100, 65).collidepoint(e.pos) else False
            
            # FIX HƯỚNG CUỘN: Lăn xuống (5) tăng scroll, Lăn lên (4) giảm scroll
            if e.button == 4: chat_scroll = max(0, chat_scroll - 50)
            if e.button == 5: chat_scroll = min(max(0, chat_h - chat_c.height), chat_scroll + 50)

        if e.type == pygame.KEYDOWN and in_act:
            if e.key == pygame.K_BACKSPACE: user_in = user_in[:-1]
            elif e.key == pygame.K_RETURN and not ai_is_thinking and user_in.strip()!="":
                chat_log.append({"s": "ME", "t": user_in}); ai_is_thinking = True
                threading.Thread(target=ask_ai_thread, args=(user_in,)).start()
                user_in = ""
                # Tự động cuộn xuống cuối khi gửi tin
                chat_scroll = max(0, chat_h - chat_c.height + 100)
        if e.type == pygame.TEXTINPUT and in_act: user_in += e.text

    pygame.display.flip(); clock.tick(60)
pygame.quit()