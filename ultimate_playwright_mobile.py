import time
import random
import os
import json
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
    if not os.path.exists("useragents.txt"):
        raise FileNotFoundError("❌ Add useragents.txt in script directory")
    with open("useragents.txt", "r") as f:
        return [ua.strip() for ua in f if ua.strip()]


USER_AGENTS = load_user_agents()


def touch_swipe(page):
    # Real swipe gesture simulation
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 300)
        start_y = random.randint(700, 900)
        end_y = random.randint(200, 400)
        page.touchscreen.tap(x, start_y)
        page.touchscreen.tap(x, end_y)
        time.sleep(random.uniform(0.4, 1.5))


def inject_fingerprint_spoof(page):
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        const original = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {
            const ctx = this.getContext("2d");
            ctx.fillStyle = "rgba(1,1,1,0.01)";
            ctx.fillRect(0,0,1,1);
            return original.apply(this, arguments);
        };

        WebGLRenderingContext.prototype.getParameter = function(param) {
            if (param === 37445) { return "ARM Mali-G78"; }
            if (param === 37446) { return "Samsung GPU"; }
            return WebGLRenderingContext.prototype.getParameter.call(this, param);
        };
    """)


def load_cookies(context, session_id):
    cookie_path = f"{SESSIONS_DIR}/session_{session_id}.json"
    if os.path.exists(cookie_path):
        with open(cookie_path, "r") as f:
            cookies = json.load(f)
            context.add_cookies(cookies)


def save_cookies(context, session_id):
    cookie_path = f"{SESSIONS_DIR}/session_{session_id}.json"
    with open(cookie_path, "w") as f:
        json.dump(context.cookies(), f)


def cleanup_session(session_id):
    cookie_path = f"{SESSIONS_DIR}/session_{session_id}.json"
    if os.path.exists(cookie_path):
        os.remove(cookie_path)


def run_session(session_id, start_url, target_url):
    ua = random.choice(USER_AGENTS)
    vp = random.choice(ANDROID_VIEWPORTS)

    print(f"\n[Session {session_id}] 🚀 Starting | UA: {ua}")

    proxy_cfg = {
        "server": f"socks5://{PROXY_HOST}:{PROXY_PORT}",
        "username": PROXY_USER,
        "password": PROXY_PASS,
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-software-rasterizer",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--no-sandbox",
                ]
            )

            context = browser.new_context(
                user_agent=ua,
                viewport=vp,
                is_mobile=True,
                has_touch=True,
                locale="en-US",
                timezone_id="Asia/Kolkata",
                proxy=proxy_cfg,
                ignore_https_errors=True,
            )

            load_cookies(context, session_id)

            page = context.new_page()
            inject_fingerprint_spoof(page)

            page.goto(start_url, wait_until="domcontentloaded")

            start_time = time.time()
            success = False

            while time.time() - start_time < MAX_WAIT_SECONDS:
                print(f"[{session_id}] URL: {page.url}")

                if page.url.startswith(target_url):
                    print(f"[{session_id}] 🎉 Redirect reached!")
                    success = True
                    break

                touch_swipe(page)
                time.sleep(random.uniform(1, 3))

            save_cookies(context, session_id)

            if not success:
                print(f"[Session {session_id}] ❌ Timeout")

            time.sleep(random.uniform(3, 5))

    except Exception as e:
        print(f"[Session {session_id}] ERROR: {e}")

    finally:
        cleanup_session(session_id)
        print(f"[Session {session_id}] 🔥 Destroyed everything")
        try:
            browser.close()
        except:
            pass


def main():
    print(f"⚡ Launching {WORKERS} parallel Android sessions…")
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(run_session, i+1, START_URL, TARGET_URL) for i in range(WORKERS)]
        for f in as_completed(futures):
            f.result()


if __name__ == "__main__":
    main()
