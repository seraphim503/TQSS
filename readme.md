
---

# QBittorrent  Stat Signature Generator

I've built a Python script that turns your live qBittorrent statistics and PC statistics into a sleek, auto-updating forum signature. 

### 1. What This Script Does

Instead of a static image, this script connects to your local qBittorrent client, reads your live data, and generates a beautiful analytics dashboard image. It securely tunnels this image to the web so you can use it in your forum profile.

- **Live Stats:** Shows real-time download/upload speeds.
    
- **Session Metrics:** Tracks data transferred in your current session.
    
- **Peak Performance:** Records your highest speeds.
    
- **Connection Status:** Dynamically checks if you are Connectable (Green) or Firewalled (Red).
    
- **Auto-Refreshing:** Automatically refreshes the image on the forum without breaking the page.

- Theres two styles to choose from:
	- 1. cyberpunk edition:
		![Recording 2026-03-01 212229](https://github.com/user-attachments/assets/9dbe6052-5e29-4deb-aa0d-01cf4d780983)

	- 2. Qbit Stat signature:
	  ![awrrr](https://files.catbox.moe/tist4f.gif)

---

### 2. What You Will Need

To run this, you need three things installed on your computer:

1. **Python 3:** To run the script.
    
2. **qBittorrent:** With the "Web UI" feature enabled in your settings.
    
3. **Cloudflared:** The free Cloudflare Tunnel tool. This is required to securely broadcast the image from your PC to the forum. Download it, extract it, and ensure it is added to your Windows PATH.
    

_(Note: You do not need to manually install Python libraries like Pillow or Flask; the script will auto-install them for you the first time you run it!)_

---

### 3. How to Install & Setup

**Step A: Configure qBittorrent**

1. Open qBittorrent and go to **Tools > Options > Web UI**.
    
2. Check the box to **"Enable the Web User Interface"**.
    
3. Note down the IP address, Port, Username, and Password. (e.g., `127.0.0.1`, Port `8080`).
    

**Step B: Prepare the Script**

1. Download the python script file to your pc.
2. Download Cloudflared to your PC (this makes the tunnel which makes hosting the image possible) :
		https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/#windows
	

**Step C: Custom Fonts (Optional but Recommended)**

The script will use standard Windows fonts by default, but for a different look, you can download a  font (like _Inter_ or _Share Tech Mono_).

1. Rename your chosen font files to `font_regular.ttf` and `font_bold.ttf`.
    
2. Place them directly inside the same folder as `Sera QB signature.py`.
    

---

### 4. How to Use

1. Open the downloaded PY file in Notepad (or any text editor).
    
2. At the very top, locate the **QB_UI CONNECTION SETTINGS**.
    
3. Change the `QB_URL`, `USER`, and `PASS` to match the Web UI settings you created in Step A.
    
4. Open your Command Prompt, navigate to your folder, and run the script by double clicking the PY file or running `python <file name>`
     
5. Watch the console. Once it connects, it will print a link that looks like this:
    
    `[img]https://random-words.trycloudflare.com/sig.png[/img]`
    
6. Copy that exact code and paste it into your  Signature box !
    

**Important:** You must keep the command prompt window open for the signature to stay online and update. If you close the window, the image will go offline. Everytime there will be a unique link created, so you have to update it. Working on a perma link update soon.

---

### 5. How to Customize (Colors, Sizes, Layout)

You don't need to be a coder to change how this looks. Everything is controlled in the easy configuration blocks at the very top of the script.

**Changing Text Sizes:**

Look for the `FONT SIZE CONFIG` section. Simply increase or decrease the numbers.

- `HEADER: 36` controls the main title size.
    
- `VALUE: 32` controls the big numbers (like your download speed).
    

**Moving Things Around:**

Look for the `3.LAYOUT & POSITIONING (X, Y)` section. The positions are controlled by `(X, Y)` coordinates.

- `X` moves the card Left and Right.
    
- `Y` moves the card Up and Down.
    

**Changing Colors:**

Look for the `4.COLORS` section. Colors use standard RGB format `(Red, Green, Blue)`. You can use any online RGB color picker to find your favorite shades.

- To change the glow of the Real-Time Flow card, change the numbers next to `"GLOW_CYAN"`.
    
- To change the background color, adjust `"APP_BG"`.


---
# 6. Others

- Im just a bba guy with 0 coding knowledge, and a gemini student account. let me know if theres issues bugs or design ideas. (DM on TBD or email burningdesire503@gmail.com)
- ar kisuna, nobody asked for this but i made it anyway. Special thanks to [Rezaul.Rabbi](https://www.torrentbd.net/account-details.php?id=273095) bhai for inspiration, Idea and guidance.
