"""外置登录服务：通过 Playwright 打开真实浏览器，让用户在扇贝完成登录后自动抓取 Cookie。"""

import threading
import time
import uuid
from pathlib import Path

import httpx

from backend.src.services.download_service import CookieManager

LOGIN_TASKS: dict[str, dict] = {}

# 登录超时时间（秒）
LOGIN_TIMEOUT = 300

# 扇贝首页；如果已经登录会直接进入已登录状态，否则会显示登录入口
LOGIN_URL = "https://www.shanbay.com"

# 持久化浏览器配置目录
PROFILE_DIR = Path(__file__).resolve().parents[3] / ".login-profile"


def _build_cookie_string(cookies: list[dict]) -> str:
    """把 Playwright 获取到的 cookies 拼成 config.ini 里使用的 Cookie 字符串。"""
    shanbay_cookies = [c for c in cookies if "shanbay.com" in c.get("domain", "")]
    shanbay_cookies.sort(
        key=lambda c: (not c.get("domain", "").startswith("."), c.get("domain", ""))
    )
    seen: set[str] = set()
    parts: list[str] = []
    for c in shanbay_cookies:
        name = c.get("name", "")
        if not name or name in seen:
            continue
        seen.add(name)
        parts.append(f"{name}={c.get('value', '')}")
    return "; ".join(parts)


def _parse_cookie_str(cookie_str: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    if not cookie_str:
        return cookies
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            cookies[key.strip()] = value.strip()
    return cookies


def _validate_cookie(cookie_str: str) -> bool:
    """用同步 HTTP 客户端验证 Cookie 是否可用（避免在 Playwright 线程里再跑 asyncio）。"""
    if not cookie_str:
        return False
    try:
        with httpx.Client(
            base_url="https://apiv3.shanbay.com",
            cookies=_parse_cookie_str(cookie_str),
            timeout=10.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Windows; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            },
        ) as client:
            resp = client.get("/wordsapp/user_material_books/current")
            if resp.status_code != 200:
                return False
            data = resp.json()
            return bool(data.get("materialbook_id"))
    except Exception as exc:  # noqa: BLE001
        print(f"Cookie 校验失败: {exc}")
        return False


def _get_auth_token(cookie_str: str) -> str | None:
    """从 Cookie 字符串中取出 auth_token 的值；没有则返回 None。"""
    if not cookie_str:
        return None
    for part in cookie_str.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip() == "auth_token" and value.strip():
                return value.strip()
    return None


def _has_auth_token(cookie_str: str) -> bool:
    """检查是否已经拿到了 auth_token（用于接口校验失败时的兜底判断）。"""
    return _get_auth_token(cookie_str) is not None


def _run_login(task_id: str) -> None:
    task = LOGIN_TASKS.get(task_id)
    if task is None:
        return

    task["status"] = "running"
    task["message"] = "正在打开浏览器，请在弹出的窗口中完成扇贝登录"

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        task["status"] = "error"
        task["message"] = (
            f"未安装 Playwright，请先在项目根目录执行：uv sync（原始错误：{exc}）"
        )
        return

    context = None
    try:
        with sync_playwright() as p:
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)

            # 优先使用系统 Edge/Chrome，避免下载浏览器；都不存在时回退到 Playwright 自带 Chromium
            for channel in ("msedge", "chrome"):
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(PROFILE_DIR),
                        channel=channel,
                        headless=False,
                        viewport={"width": 1200, "height": 800},
                        args=["--disable-blink-features=AutomationControlled"],
                    )
                    break
                except Exception:  # noqa: BLE001
                    context = None

            if context is None:
                try:
                    context = p.chromium.launch_persistent_context(
                        user_data_dir=str(PROFILE_DIR),
                        headless=False,
                        viewport={"width": 1200, "height": 800},
                        args=["--disable-blink-features=AutomationControlled"],
                    )
                except Exception as exc:  # noqa: BLE001
                    task["status"] = "error"
                    task["message"] = (
                        "无法启动浏览器，请确认已安装 Edge/Chrome，"
                        "或执行 `uv run playwright install chromium`。"
                        f"原始错误: {exc}"
                    )
                    return

            page = context.pages[0] if context.pages else context.new_page()
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
            # 记录打开页面时已有的 auth_token，避免把旧 Cookie 误判为新登录
            initial_auth_token = _get_auth_token(
                _build_cookie_string(context.cookies())
            )

            deadline = time.time() + LOGIN_TIMEOUT
            while time.time() < deadline:
                # 如果用户手动关闭了窗口，主动结束
                if not context.pages:
                    task["status"] = "error"
                    task["message"] = "登录窗口已关闭，未获取到 Cookie"
                    return

                cookie_str = _build_cookie_string(context.cookies())
                if _validate_cookie(cookie_str):
                    cookie_manager = CookieManager()
                    cookie_manager.save_cookie("COOKIE", cookie_str)
                    task["status"] = "success"
                    task["message"] = "登录成功，Cookie 已自动保存并生效"
                    return

                current_auth_token = _get_auth_token(cookie_str)

                if current_auth_token and current_auth_token != initial_auth_token:
                    cookie_manager = CookieManager()
                    cookie_manager.save_cookie("COOKIE", cookie_str)
                    task["status"] = "success"
                    task["message"] = (
                        "已获取登录 Cookie；如果学习时仍提示失败，请重新登录一次"
                    )
                    return

                task["message"] = "等待登录完成…"
                time.sleep(2)

            task["status"] = "error"
            task["message"] = "登录超时，请重新尝试"
    except Exception as exc:  # noqa: BLE001
        task["status"] = "error"
        task["message"] = f"登录失败: {exc}"
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:  # noqa: BLE001
                pass


def start_login() -> str:
    """启动一个后台线程执行外置登录，返回 task_id 供前端轮询。"""
    task_id = uuid.uuid4().hex
    LOGIN_TASKS[task_id] = {
        "status": "pending",
        "message": "准备启动浏览器…",
    }
    thread = threading.Thread(target=_run_login, args=(task_id,), daemon=True)
    thread.start()
    return task_id


def get_login_task(task_id: str) -> dict | None:
    return LOGIN_TASKS.get(task_id)
