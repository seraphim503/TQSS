import os
import time
import subprocess
import threading
import io
import re
from datetime import datetime
from flask import Flask, Response
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

# ==========================================================
# === 1. QB_UI CONNECTION SETTINGS                       ===
# ==========================================================
QB_URL = "http://127.1.1.1:8080" 
USER = "seraphim"               
PASS = ""                       

# ==========================================================
# === 2. FONT SIZE CONFIGURATION                         ===
# ==========================================================
FONT_CONFIG = {
    "HEADER":  36,  
    "VALUE":   32,  
    "LABEL":   20,  
    "CAPTION": 16   
}

# ==========================================================
# === 3. LAYOUT & POSITIONING (X, Y)                     ===
# ==========================================================
# Change these numbers to move elements around the image
LAYOUT = {
    "HEADER":   (40, 35),
    "CARD_1":   (40, 120),   # Real-Time Flow Card
    "CARD_2":   (40, 270),   # Peak Performance Card
    "CARD_3":   (520, 120),  # Session Metrics Card
    "FOOTER_L": (40, 430),   # DHT Nodes
    "FOOTER_R": (810, 430)   # Time Synced
}

# ==========================================================
# === 4.                  COLORS                         ===
# ==========================================================
COLORS = {
    "APP_BG":       (10, 14, 22),      # Deep Dark Navy Background
    "GLASS_FILL":   (255, 255, 255, 8),# Barely-there frosted glass
    "TEXT_MAIN":    (255, 255, 255),   # Solid White for numbers
    "TEXT_DIM":     (160, 170, 180),   # Cool grey for labels
    
    "GLOW_CYAN":    (0, 220, 255),     
    "GLOW_MAGENTA": (255, 0, 150),     
    "GLOW_PURPLE":  (160, 50, 255),    
    
    "STATUS_GOOD":  (0, 255, 128),     # Connectable
    "STATUS_BAD":   (255, 50, 50)      # Firewalled
}

# === CORE SYSTEM ===
app = Flask(__name__)
session = requests.Session()
latest_frame = None
frame_lock = threading.Lock()
peak_dl, peak_up = 0, 0

def get_fallback_font(size, is_bold=False):
    custom_name = "font_bold.ttf" if is_bold else "font_regular.ttf"
    try: return ImageFont.truetype(custom_name, size)
    except IOError: pass
        
    fallbacks = [
        "lucon.ttf", 
        "timesbd.ttf" if is_bold else "times.ttf",
        "segoeuib.ttf" if is_bold else "segoeui.ttf",
        "arialbd.ttf" if is_bold else "arial.ttf"
    ]
    for font in fallbacks:
        try: return ImageFont.truetype(font, size)
        except IOError: continue
            
    return ImageFont.load_default()

def get_qb_data():
    global peak_dl, peak_up
    try:
        session.post(f"{QB_URL}/api/v2/auth/login", data={'username': USER, 'password': PASS}, timeout=2)
        res = session.get(f"{QB_URL}/api/v2/transfer/info", timeout=2).json()
        
        dl_mbps = (res['dl_info_speed'] * 8) / 1000000
        up_mbps = (res['up_info_speed'] * 8) / 1000000
        
        if dl_mbps > peak_dl: peak_dl = dl_mbps
        if up_mbps > peak_up: peak_up = up_mbps
        
        c_status = res.get('connection_status', 'unknown')
        if c_status == 'connected':
            status_text, status_color = "CONNECTABLE", COLORS["STATUS_GOOD"]
        elif c_status == 'firewalled':
            status_text, status_color = "FIREWALLED", COLORS["STATUS_BAD"]
        else:
            status_text, status_color = c_status.upper(), COLORS["TEXT_DIM"]
            
        return {
            "dl": f"{dl_mbps:.2f} Mbps", "up": f"{up_mbps:.2f} Mbps",
            "p_dl": f"{peak_dl:.2f} Mbps", "p_up": f"{peak_up:.2f} Mbps",
            "total_dl": f"{res['dl_info_data'] / 1024**3:.1f} GB",
            "total_up": f"{res['up_info_data'] / 1024**3:.1f} GB",
            "nodes": res['dht_nodes'],
            "status_text": status_text,
            "status_color": status_color
        }
    except Exception as e:
        return str(e)

def draw_glass_card(bg_img, x, y, w, h, title, font_cap, glow_color):
    glow_layer = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    glow_draw.rounded_rectangle([x-2, y-2, x+w+2, y+h+2], radius=18, outline=(*glow_color, 120), width=6)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=10))
    
    card_layer = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card_layer)
    card_draw.rounded_rectangle([x, y, x+w, y+h], radius=15, fill=COLORS["GLASS_FILL"], outline=(*glow_color, 180), width=1)
    card_draw.text((x+20, y+15), title, font=font_cap, fill=(*glow_color, 255))
    
    bg_img.alpha_composite(glow_layer)
    bg_img.alpha_composite(card_layer)

def render_loop():
    global latest_frame
    f_reg = get_fallback_font(FONT_CONFIG["VALUE"], False)
    f_bold = get_fallback_font(FONT_CONFIG["VALUE"], True)
    f_title = get_fallback_font(FONT_CONFIG["HEADER"], True)
    f_lbl = get_fallback_font(FONT_CONFIG["LABEL"], False)
    f_cap = get_fallback_font(FONT_CONFIG["CAPTION"], True)

    while True:
        data = get_qb_data()
        
        base_img = Image.new('RGBA', (1050, 480), color=(*COLORS["APP_BG"], 255))
        draw = ImageDraw.Draw(base_img)
        
        # Header text
        draw.text(LAYOUT["HEADER"], "Transfer Analytics", font=f_title, fill=(*COLORS["GLOW_PURPLE"], 255))
        draw.line([(40, 95), (1010, 95)], fill=(255, 255, 255, 20), width=1)

        if isinstance(data, dict):
            # CARD 1: Flow (Cyan)
            c1_x, c1_y = LAYOUT["CARD_1"]
            draw_glass_card(base_img, c1_x, c1_y, 450, 130, "REAL-TIME FLOW", f_cap, COLORS["GLOW_CYAN"])
            draw.text((c1_x+20, c1_y+45), "Download", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c1_x+20, c1_y+75), data["dl"], font=f_bold, fill=(*COLORS["STATUS_GOOD"], 255))
            draw.text((c1_x+220, c1_y+45), "Upload", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c1_x+220, c1_y+75), data["up"], font=f_bold, fill=(*COLORS["STATUS_BAD"], 255))

            # CARD 2: Peaks (Magenta)
            c2_x, c2_y = LAYOUT["CARD_2"]
            draw_glass_card(base_img, c2_x, c2_y, 450, 130, "PEAK PERFORMANCE", f_cap, COLORS["GLOW_MAGENTA"])
            draw.text((c2_x+20, c2_y+45), "Max DL", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c2_x+20, c2_y+75), data["p_dl"], font=f_bold, fill=(*COLORS["TEXT_MAIN"], 255))
            draw.text((c2_x+220, c2_y+45), "Max UL", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c2_x+220, c2_y+75), data["p_up"], font=f_bold, fill=(*COLORS["TEXT_MAIN"], 255))

            # CARD 3: Session (Purple)
            c3_x, c3_y = LAYOUT["CARD_3"]
            draw_glass_card(base_img, c3_x, c3_y, 490, 280, "SESSION METRICS", f_cap, COLORS["GLOW_PURPLE"])
            draw.text((c3_x+20, c3_y+45), "Data Downloaded", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c3_x+20, c3_y+75), data["total_dl"], font=f_bold, fill=(*COLORS["TEXT_MAIN"], 255))
            draw.text((c3_x+20, c3_y+125), "Data Uploaded", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c3_x+20, c3_y+155), data["total_up"], font=f_bold, fill=(*COLORS["TEXT_MAIN"], 255))
            
            # Connection Status
            draw.text((c3_x+20, c3_y+215), "Status:", font=f_lbl, fill=(*COLORS["TEXT_DIM"], 255))
            draw.text((c3_x+110, c3_y+212), data['status_text'], font=f_bold, fill=(*data['status_color'], 255))

            # Footer
            draw.text(LAYOUT["FOOTER_L"], f"DHT: {data['nodes']} NODES", font=f_cap, fill=(*COLORS["GLOW_CYAN"], 255))
            draw.text(LAYOUT["FOOTER_R"], f"SYNCED: {datetime.now().strftime('%I:%M:%S %p')}", font=f_cap, fill=(*COLORS["TEXT_DIM"], 255))
        else:
            draw.text((50, 220), f"ERROR: {data}", font=f_lbl, fill=(255, 50, 50, 255))

        final_img = base_img.convert('RGB')
        buf = io.BytesIO()
        final_img.save(buf, format='JPEG', quality=85)
        
        with frame_lock: 
            latest_frame = buf.getvalue()
        time.sleep(0.5)

def generate_stream():
    while True:
        frame = None
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.5)

@app.route('/sig.jpg')
@app.route('/sig.png')
def get_sig():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def cloudflare_manager():
    print("Starting Cloudflare Tunnel...")
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://127.0.0.1:5000"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in iter(proc.stdout.readline, ''):
            if not line: break
            match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
            if match:
                print(f"\n======================================================")
                print(f"LIVE STREAM ONLINE! PASTE THIS INTO YOUR FORUM:")
                print(f"[img]{match.group(1)}/sig.png[/img]")
                print(f"======================================================\n")
                break
    except FileNotFoundError:
        print("ERROR: 'cloudflared' not found.")

if __name__ == '__main__':
    threading.Thread(target=render_loop, daemon=True).start()
    threading.Thread(target=cloudflare_manager, daemon=True).start()
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, threaded=True)