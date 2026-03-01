import os
import time
import subprocess
import threading
import io
import re
from datetime import datetime
from flask import Flask, Response

# === 1. AUTOMATIC DEPENDENCY HANDLING ===
def install_dependencies():
    import sys
    required = {'Pillow', 'psutil', 'flask'}
    try:
        import PIL, psutil, flask
    except ImportError:
        print("Installing missing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *required])

install_dependencies()
import psutil
from PIL import Image, ImageDraw, ImageFont

# Try to load NVIDIA tools (Fails gracefully if not installed/available)
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False

# ==========================================================
# === 2. SYSTEM CONFIGURATION                            ===
# ==========================================================
# Change this if your Task Manager says "Wi-Fi" instead of "Ethernet"
ADAPTER = "Ethernet"
USERNAME = "Seraphim"

# ==========================================================
# === 3. FONT SIZE CONFIGURATION                         ===
# ==========================================================
FONT_CONFIG = {
    "HEADER":  44,  
    "VALUE":   34,  
    "LABEL":   34,  
    "CAPTION": 24   
}

# ==========================================================
# === 4. LAYOUT & POSITIONING                            ===
# ==========================================================
LAYOUT = {
    "CANVAS": (1300, 500),
    "HEADER": (60, 40),
    "DOT":    (1100, 52),
    
    # Grid System (X coordinates)
    "COL_L_X": 60,   # Left labels
    "VAL_L_X": 200,  # Left values
    "COL_R_X": 690,  # Right labels
    "VAL_R_X": 850,  # Right values
    
    # Grid System (Y coordinates)
    "ROW_HEAD": 140,
    "ROW_1":    210,
    "ROW_2":    280,
    "ROW_3":    350,
    "ROW_4":    420
}

# ==========================================================
# === 5. CYBERPUNK COLOR PALETTE                         ===
# ==========================================================
COLORS = {
    "APP_BG":      (0, 0, 0),         # AMOLED Black
    "BORDER":      (50, 55, 65),      # Dark Gray lines
    "NEON_CYAN":   (0, 255, 255),     
    "NEON_ORANGE": (255, 140, 0),     
    "NEON_RED":    (255, 50, 50),     
    "ACCENT_BLUE": (100, 180, 255),   # CPU color
    "ACCENT_YEL":  (255, 200, 80),    # RAM color
    "ACCENT_GRN":  (80, 230, 120),    # Download color
    "TEXT_MAIN":   (240, 240, 240),   # White text
    "TEXT_DIM":    (130, 140, 150),   # Gray text
    "DOT_OFF":     (0, 60, 60)        # Dim cyan for blinking effect
}

# === CORE SYSTEM ===
app = Flask(__name__)
latest_frame = None
frame_lock = threading.Lock()

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

def format_bytes(b):
    if b >= 1024**4: return f"{round(b / (1024**4), 1)} TB"
    return f"{round(b / (1024**3), 1)} GB"

def get_uptime():
    uptime_seconds = time.time() - psutil.boot_time()
    days = int(uptime_seconds // (24 * 3600))
    uptime_seconds %= (24 * 3600)
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    if days > 0: return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m"

def render_loop():
    global latest_frame
    f_reg = get_fallback_font(FONT_CONFIG["VALUE"], False)
    f_bold = get_fallback_font(FONT_CONFIG["VALUE"], True)
    f_title = get_fallback_font(FONT_CONFIG["HEADER"], True)
    f_lbl = get_fallback_font(FONT_CONFIG["LABEL"], False)
    
    blink_state = True

    while True:
        # --- 1. Gather Stats Safely ---
        net1 = psutil.net_io_counters(pernic=True)
        time.sleep(1) # Paces the loop and measures network delta
        net2 = psutil.net_io_counters(pernic=True)
        
        try:
            dl_mbps = ((net2[ADAPTER].bytes_recv - net1[ADAPTER].bytes_recv) * 8) / 1000000
            up_mbps = ((net2[ADAPTER].bytes_sent - net1[ADAPTER].bytes_sent) * 8) / 1000000
        except KeyError:
            dl_mbps = up_mbps = 0.0

        cpu_percent = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        
        gpu_stat = "N/A"
        if HAS_NVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_stat = f"{pynvml.nvmlDeviceGetUtilizationRates(handle).gpu}%"
            except Exception:
                gpu_stat = "ERR"

        total_used = total_free = 0
        for part in psutil.disk_partitions(all=False):
            if 'cdrom' in part.opts or part.fstype == '': continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_used += usage.used
                total_free += usage.free
            except PermissionError:
                continue

        # Toggle blink state
        blink_state = not blink_state

        # --- 2. Draw Image ---
        img = Image.new('RGB', LAYOUT["CANVAS"], color=COLORS["APP_BG"])
        draw = ImageDraw.Draw(img)
        
        # Borders
        draw.rectangle([(20, 20), (LAYOUT["CANVAS"][0]-20, LAYOUT["CANVAS"][1]-20)], outline=COLORS["BORDER"], width=3)
        
        # Corrected Neon Corners Logic
        c_len = 40
        canvas_w, canvas_h = LAYOUT["CANVAS"]
        corners = [
            (20, 20), (canvas_w-20, 20), 
            (20, canvas_h-20), (canvas_w-20, canvas_h-20)
        ]
        
        for x, y in corners:
            # Determine direction based on which corner it is
            dx = 1 if x < canvas_w / 2 else -1
            dy = 1 if y < canvas_h / 2 else -1
            
            # Draw the two lines for the corner
            draw.line([(x, y), (x + c_len * dx, y)], fill=COLORS["NEON_CYAN"], width=6)
            draw.line([(x, y), (x, y + c_len * dy)], fill=COLORS["NEON_CYAN"], width=6)

        # Header & Blinking Dot
        draw.text(LAYOUT["HEADER"], "// STATUS //", font=f_title, fill=COLORS["NEON_CYAN"])
        dot_color = COLORS["NEON_CYAN"] if blink_state else COLORS["DOT_OFF"]
        dx, dy = LAYOUT["DOT"]
        draw.ellipse([(dx, dy), (dx+18, dy+18)], fill=dot_color)

        # Dividers
        draw.line([(20, 110), (LAYOUT["CANVAS"][0]-20, 110)], fill=COLORS["BORDER"], width=3)
        draw.line([(650, 110), (650, LAYOUT["CANVAS"][1]-20)], fill=COLORS["BORDER"], width=3)

        # Left Column (Systems)
        lx, vx = LAYOUT["COL_L_X"], LAYOUT["VAL_L_X"]
        draw.text((lx, LAYOUT["ROW_HEAD"]), "[ CORE_SYSTEMS ]", font=f_bold, fill=COLORS["NEON_ORANGE"])
        
        draw.text((lx, LAYOUT["ROW_1"]), "CPU:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vx, LAYOUT["ROW_1"]), f"{cpu_percent}%", font=f_bold, fill=COLORS["ACCENT_BLUE"])
        
        draw.text((lx, LAYOUT["ROW_2"]), "GPU:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vx, LAYOUT["ROW_2"]), f"{gpu_stat}", font=f_bold, fill=COLORS["TEXT_MAIN"])
        
        draw.text((lx, LAYOUT["ROW_3"]), "RAM:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        ram_text = f"{round(mem.used / (1024**3), 1)} / {round(mem.total / (1024**3), 1)} GB ({mem.percent}%)"
        draw.text((vx, LAYOUT["ROW_3"]), ram_text, font=f_bold, fill=COLORS["ACCENT_YEL"])
        
        draw.text((lx, LAYOUT["ROW_4"]), "Disk:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vx, LAYOUT["ROW_4"]), f"{format_bytes(total_used)} used", font=f_bold, fill=COLORS["TEXT_MAIN"])

        # Right Column (Network)
        rx, vrx = LAYOUT["COL_R_X"], LAYOUT["VAL_R_X"]
        draw.text((rx, LAYOUT["ROW_HEAD"]), "[ NETWORK_UPLINK ]", font=f_bold, fill=COLORS["NEON_ORANGE"])
        
        draw.text((rx, LAYOUT["ROW_1"]), "DL:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vrx, LAYOUT["ROW_1"]), f"{round(dl_mbps, 2)} Mbps", font=f_bold, fill=COLORS["ACCENT_GRN"])
        
        draw.text((rx, LAYOUT["ROW_2"]), "UP:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vrx, LAYOUT["ROW_2"]), f"{round(up_mbps, 2)} Mbps", font=f_bold, fill=COLORS["NEON_RED"])
        
        draw.text((rx, LAYOUT["ROW_3"]), "Uptime:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vrx, LAYOUT["ROW_3"]), get_uptime(), font=f_bold, fill=COLORS["TEXT_MAIN"])
        
        draw.text((rx, LAYOUT["ROW_4"]), "Time:", font=f_lbl, fill=COLORS["TEXT_DIM"])
        draw.text((vrx, LAYOUT["ROW_4"]), datetime.now().strftime("%I:%M:%S %p"), font=f_bold, fill=COLORS["NEON_CYAN"])

        # Convert and save frame
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        
        with frame_lock:
            latest_frame = buf.getvalue()

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
    print("Initializing Cloudflare Tunnel...")
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
                print(f"TQSS Cyberpunk version ONLINE! PASTE THIS INTO YOUR signature:")
                print(f"[img]{match.group(1)}/sig.png[/img]")
                print(f"======================================================\n")
                break
    except FileNotFoundError:
        print("ERROR: 'cloudflared' not found. Ensure it is in your PATH.")

if __name__ == '__main__':
    threading.Thread(target=render_loop, daemon=True).start()
    threading.Thread(target=cloudflare_manager, daemon=True).start()
    
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, threaded=True)