import time
import random
import os
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

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
# PRIVIOXY CONFIG TEMPLATE
# =============================
PRIVOXY_TEMPLATE = """
forward-socks5t / {proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port} .
allow CONNECT
logfile privoxy{port}.log
listen-address 127.0.0.1:{port}
"""

def start_privoxy(port, proxy_user, proxy_pass):
    cfg_path = f"privoxy_{port}.conf"
    cfg_content = PRIVOXY_TEMPLATE.format(
        proxy_user=proxy_user,
        proxy_pass=proxy_pass,
        proxy_host=PROXY_HOST,
        proxy_port=PROXY_PORT,
        port=port
    )
    with open(cfg_path, "w") as cfg:
        cfg.write(cfg_content)

    subprocess.Popen(["privoxy", cfg_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"🟢 Privoxy running on: http://127.0.0.1:{port}")

# =============================
# MAIN ROUTINE
# =============================
def run_session(session_id, start_url, target_url):
    local_port = 9000 + session_id
    rotating_user = f"{PROXY_USER}-sid{session_id}-{random.randint(1000,9999)}"

    start_privoxy(local_port, rotating_user, PROXY_PASS)

    ua = random.choice(USER_AGENTS)
    vp = random.choice(ANDROID_VIEWPORTS)

    print(f"\n[Session {session_id}] 🚀 Started | UA: {ua}")

    proxy_cfg = {"server": f"http://127.0.0.1:{local_port}"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )

            context = browser.new_context(
                user_agent=ua,
                viewport=vp,
                is_mobile=True,
                has_touch=True,
                ignore_https_errors=True,
                locale="en-US",
                timezone_id="Asia/Kolkata",
                proxy=proxy_cfg,
            )

            page = context.new_page()
            page.goto(start_url, wait_until="domcontentloaded")

            start_time = time.time()
            success = False

            while time.time() - start_time < MAX_WAIT_SECONDS:
                print(f"[Session {session_id}] URL: {page.url}")

                if page.url.startswith(target_url):
                    print(f"[Session {session_id}] 🎉 Redirect Success")
                    success = True
                    break

                time.sleep(random.uniform(1, 3))

            if not success:
                print(f"[Session {session_id}] ❌ Timeout")

            time.sleep(random.uniform(3, 6))

    except Exception as e:
        print(f"[Session {session_id}] ERROR: {e}")

    finally:
        print(f"[Session {session_id}] 🔥 Completed")


def main():
    print(f"⚡ Launching {WORKERS} rotating proxy sessions…")
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(run_session, i+1, START_URL, TARGET_URL) for i in range(WORKERS)]
        for f in as_completed(futures):
            f.result()


if __name__ == "__main__":
    main()
