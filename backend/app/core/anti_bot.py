import asyncio
import random
import json
from typing import Optional
from fake_useragent import UserAgent

ua = UserAgent()

COMMON_ACCEPT_LANGUAGES = [
    "en-IN,en;q=0.9,hi;q=0.8",
    "en-US,en;q=0.9,en-IN;q=0.8",
    "en-GB,en;q=0.9,en-IN;q=0.8",
    "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
]

COMMON_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]

COMMON_TIMEZONES = [
    "Asia/Kolkata",
    "Asia/Calcutta",
]


def get_random_headers() -> dict:
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(COMMON_ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": str(random.randint(0, 1)),
    }


def get_random_viewport() -> dict:
    return random.choice(COMMON_VIEWPORTS)


def get_random_timezone() -> str:
    return random.choice(COMMON_TIMEZONES)


async def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.5):
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def micro_delay():
    await asyncio.sleep(random.uniform(0.1, 0.4))


async def configure_stealth_page(page):
    """Apply stealth settings to a Playwright page."""
    viewport = get_random_viewport()
    await page.set_viewport_size(viewport)

    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
        });
    """)

    await page.set_extra_http_headers({
        "Accept-Language": random.choice(COMMON_ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
    })


async def simulate_human_scroll(page, scroll_count: int = 3):
    for _ in range(scroll_count):
        scroll_y = random.randint(200, 600)
        await page.evaluate(f"window.scrollBy(0, {scroll_y})")
        await micro_delay()


async def simulate_human_mouse_movement(page):
    viewport = page.viewport_size or {"width": 1280, "height": 720}
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, viewport["width"] - 100)
        y = random.randint(100, viewport["height"] - 100)
        await page.mouse.move(x, y)
        await micro_delay()


def get_playwright_launch_args() -> dict:
    return {
        "headless": True,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
            "--lang=en-IN",
            f"--window-size={random.choice([1920, 1440, 1366])},{random.choice([1080, 900, 768])}",
        ],
    }
