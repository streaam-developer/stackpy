import time
import random
import os
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

START_URL = "https://linkcents.com"
TARGET_URL = "https://testss-3c9.pages.dev/"
WORKERS = 3
MAX_WAIT_SECONDS = 180

PROXY_HOST = "dc.decodo.com"
PROXY_PORT = 10000
PROXY_USER = "user-spvsdflcwv-country-in"
PROXY_PASS = "p2T~QluX2tw4ch4Caj"

ANDROID_VIEWPORTS = [
    {"width": 412, "height": 915},
    {"width": 360, "height": 760},
    {"width": 414, "height": 896},
    {"width": 390, "height": 844},
]

if not os.path.exists("android_uas.txt"):
    raise FileNotFoundError("❌ Add android_uas.txt first")

def load_user_agents():
    with open("android_uas.txt", "r") as f:
        return [ua.strip() for ua in f if ua.strip()]

USER_AGENTS = load_user_agents()

def run_session(session_id, start_url, target_url):
    rotating_user = f"{PROXY_USER}-sid{session_id}-{random.randint(1000,9999)}"

    proxy_cfg = {
        "server": f"socks5://{rotating_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    }

    ua = random.choice(USER_AGENTS)
    vp = random.choice(ANDROID_VIEWPORTS)

    print(f"\n[Session {session_id}] 🚀 Starting | {proxy_cfg['server']}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

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

            time.sleep(random.uniform(3, 5))

    except Exception as e:
        print(f"[Session {session_id}] ERROR: {e}")

    finally:
        print(f"[Session {session_id}] 🔥 Closed")

def main():
    print(f"⚡ Launching {WORKERS} SOCKS5 rotating sessions…")
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(run_session, i+1, START_URL, TARGET_URL) for i in range(WORKERS)]
        for f in as_completed(futures):
            f.result()

if __name__ == "__main__":
    main()
