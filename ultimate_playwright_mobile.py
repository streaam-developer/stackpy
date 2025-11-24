import time
import random
import os
import json
import socket
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from socks import socksocket, SOCKS5
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# =============================
# CONFIG
# =============================
START_URL = "https://linkcents.com"
TARGET_URL = "https://testss-3c9.pages.dev/"
WORKERS = 3
MAX_WAIT_SECONDS = 180

PROXY_HOST = "dc.decodo.com"
PROXY_PORT = 10000
PROXY_USER = "user-spvsdflcwv-country-in"
PROXY_PASS = "p2T~QluX2tw4ch4Caj"

SESSIONS_DIR = "sessions"
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

ANDROID_VIEWPORTS = [
    {"width": 412, "height": 915},
    {"width": 360, "height": 760},
    {"width": 414, "height": 896},
    {"width": 390, "height": 844},
]

def load_user_agents():
    if not os.path.exists("android_uas.txt"):
        raise FileNotFoundError("❌ Add android_uas.txt")
    with open("android_uas.txt", "r") as f:
        return [ua.strip() for ua in f if ua.strip()]

USER_AGENTS = load_user_agents()

# =============================
# SOCKS5 → HTTP CONVERTER
# =============================
class ProxyHandler(BaseHTTPRequestHandler):
    def do_CONNECT(self):
        self._proxy_request()

    def do_GET(self):
        self._proxy_request()

    def _proxy_request(self):
        url = self.path
        parsed = urlparse(url if "://" in url else "http://" + url)

        sock = socksocket()
        sock.set_proxy(SOCKS5, PROXY_HOST, PROXY_PORT, True, self.server.proxy_user, self.server.proxy_pass)

        try:
            sock.connect((parsed.hostname, parsed.port or 80))
            self.send_response(200)
            self.end_headers()

            if self.command == "CONNECT":
                self.connection.setblocking(False)
                while True:
                    data = self.connection.recv(4096)
                    if not data: break
                    sock.send(data)
            else:
                request = f"{self.command} {parsed.path} HTTP/1.1\r\nHost: {parsed.hostname}\r\n\r\n"
                sock.send(request.encode())
                while True:
                    data = sock.recv(4096)
                    if not data: break
                    self.wfile.write(data)
        except Exception:
            self.send_error(502)
        finally:
            sock.close()

def start_local_proxy(port, user, password):
    server = HTTPServer(("127.0.0.1", port), ProxyHandler)
    server.proxy_user = user
    server.proxy_pass = password

    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🟢 Local HTTP Proxy running: http://127.0.0.1:{port}")

# =============================
# MAIN ROUTINE
# =============================
def run_session(session_id, start_url, target_url):
    local_port = 9000 + session_id  # dynamic port

    # Unique proxy username for new IP
    rotating_user = f"{PROXY_USER}-sid{session_id}-{random.randint(1000,9999)}"

    # start converter
    start_local_proxy(local_port, rotating_user, PROXY_PASS)

    ua = random.choice(USER_AGENTS)
    vp = random.choice(ANDROID_VIEWPORTS)

    print(f"\n[Session {session_id}] 🚀 Starting | UA: {ua}")

    proxy_cfg = {"server": f"http://127.0.0.1:{local_port}"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=ua,
                viewport=vp,
                is_mobile=True,
                has_touch=True,
                locale="en-US",
                timezone_id="Asia/Kolkata",
                proxy=proxy_cfg,
            )

            page = context.new_page()
            page.goto(start_url, wait_until="domcontentloaded")

            start_time = time.time()
            success = False

            while time.time() - start_time < MAX_WAIT_SECONDS:
                print(f"[{session_id}] URL: {page.url}")
                if page.url.startswith(target_url):
                    print(f"[{session_id}] 🎉 Redirect success")
                    success = True
                    break

                time.sleep(random.uniform(1, 3))

            if not success:
                print(f"[Session {session_id}] ❌ Timeout")

            time.sleep(random.uniform(3, 6))

    except Exception as e:
        print(f"[Session {session_id}] ERROR: {e}")

    finally:
        print(f"[Session {session_id}] 🔥 Done")


def main():
    print(f"⚡ Launching {WORKERS} rotating proxy sessions…")
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(run_session, i+1, START_URL, TARGET_URL) for i in range(WORKERS)]
        for f in as_completed(futures):
            f.result()


if __name__ == "__main__":
    main()
