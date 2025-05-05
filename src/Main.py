# -*- coding: utf-8 -*-
"""
pip install selenium webdriver-manager

运行：
    uv run src/Main.py
或  python src/Main.py
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from tqdm import tqdm
import time

import argparse
# ─────────────── 配 置 ───────────────
SERVICE_ID = "10339027"   # ← 换成你的
LOCATION_ID = "10187259"  # ← 换成你的
TARGET_DATE = "2025-06-07" # ← 想要点击的日期；留空则只打印可用日期
TIMEOUT     = 20           # Selenium 显式等待秒数
BREAK_INTERVAL = 5            # 检查间隔秒数
RESTART_INTERVAL = 35         # 重启间隔秒数
# ─────────────────────────────────────

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────── 工具：点击 Shadow DOM 内元素 ───────────
def click_in_shadow(driver, host_css, inner_css, timeout=TIMEOUT):
    """在 WebComponent 的 shadowRoot 内查找并点击子元素"""
    wait = WebDriverWait(driver, timeout)


    # 1️⃣ host 节点
    host = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "zms-appointment")
    ))

    # 2️⃣ Vue 把 shadowRoot 塞给它以后，再去拿 root
    root = wait.until(lambda d: host.shadow_root)

    # 3️⃣ 再等按钮真正出现在 root 里
    btn = wait.until(lambda d: root.find_element(By.CSS_SELECTOR, "button.button-next"))
    wait.until(EC.element_to_be_clickable(btn))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", btn)
    btn.click()

def find_element_in_shadow(driver, host_css, inner_css, timeout=TIMEOUT):
    """在 WebComponent 的 shadowRoot 内查找元素"""
    wait = WebDriverWait(driver, timeout)

    # 1️⃣ host 节点
    host = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, host_css)
    ))

    # 2️⃣ Vue 把 shadowRoot 塞给它以后，再去拿 root
    root = wait.until(lambda d: host.shadow_root)

    # 3️⃣ 再等element真正出现在 root 里
    element = wait.until(lambda d: root.find_element(By.CSS_SELECTOR, inner_css))
    wait.until(EC.element_to_be_clickable(element))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", element) # 滚动到可见位置
    return element

def is_day_enabled(root, day: int) -> bool:
    """
    在已定位到的日历 shadow_root（或 container）中，
    查找日期为 day 的按钮并返回它是否可用（enabled）。
    """
    try:
        # 1) 用 XPath 找到包含数字的 <div>，然后拿它的父 <button>
        btn = root.find_element(
            By.XPATH,
            f".//button[.//div[text()='{day}']]"
        )
    except NoSuchElementException:
        # 找不到这样的按钮，说明日历里根本没有这个日期
        return False

    # 2) 两种方式判断是否可用：
    # 方法 A: Selenium 提供的 is_enabled()
    log.info("日期 %s 可用: %s", day, btn.is_enabled())
    return btn.is_enabled()

# ─────────── 工具：播放警告 ───────────
def alert_sound():
    """播放警告音效"""
    import winsound
    frequency = 440  # Set Frequency To 440 Hertz
    duration = 1000  # Set Duration To 1000 ms == 1 second
    while True:
        winsound.Beep(frequency, duration)


# ─────────── 打开浏览器 ───────────
def open_browser():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--log-level=3")                          # 静音 USB 报警
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install(), log_level="INFO")
    return webdriver.Chrome(service=service, options=opts)

# ───────────  单次检查 ───────────
def check_once(driver, date: str):
    url = (
        "https://www48.muenchen.de/buergeransicht"
        f"#/services/{SERVICE_ID}/locations/{LOCATION_ID}"
    )
    log.info("打开页面: %s", url)
    driver.get(url)

    try:
        # 1) 组件加载
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "zms-appointment"))
        )
        log.info("zms-appointment 组件已加载")

        # 2) 点击『Weiter zur Terminsuche』/ 下一步
        log.info("点击『Weiter / Nächster Schritt』按钮 …")
        click_in_shadow(
            driver,
            host_css="zms-appointment",          # 不变
            inner_css="button.button-next",      # ⬅︎✅ 正确 selector
        )

        # 3) 读取日历：所有可用日期按钮带 data-date 属性且未 disabled
        wait = WebDriverWait(driver, TIMEOUT)
        # root = wait.until(lambda d: host.shadow_root)
        host = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "zms-appointment")))
        log.info("zms-appointment 组件已加载")
        # 等 shadowRoot 出现
        shadow = driver.execute_script("return arguments[0].shadowRoot", host)
        log.info("shadowRoot 已加载")
        # 等日历组件出现

        # 日历组件 <zms-calendar> 也在 Shadow DOM
        root = wait.until(lambda d: host.shadow_root)
        calendar = find_element_in_shadow(
            driver,
            host_css="zms-appointment",
            inner_css="table",           # 只为了拿到 shadowRoot
        )
        log.info("日历组件已加载")
        
        available_dates = []
        for day in range(1, 32):
            if is_day_enabled(calendar, day):
                available_dates.append(day)
        log.info("本月可预约日期: %s", ", ".join(map(str, available_dates)) or "— 无 —")
        
        if available_dates:
            alert_sound()
            log.info("有可预约日期！")


    except Exception as e:
        log.exception("执行过程中出错: %s", e)
    finally:
        log.info("结束")


# ─────────── 主流程 ───────────
def main():
    log.info("开始检查 …")
    driver = open_browser()
    while True:
        try:
                driver.refresh()
                log.info("检查可预约日期 …")
                check_once(driver, TARGET_DATE)

                # 等待一段时间后再检查
                log.info("等待 %s 秒后继续 …", BREAK_INTERVAL)
                for _ in tqdm(range(int(10 * BREAK_INTERVAL)), desc="等待中",ncols=80, bar_format="{l_bar}{bar}| [{elapsed}<{remaining}]"):
                    time.sleep(BREAK_INTERVAL / 30)
                # 休息完了，刷新页面
                driver.refresh()
                log.info("刷新页面 …")
        except KeyboardInterrupt:
            log.info("检测中断，退出 …")
        except Exception as e:
            log.exception("执行过程中出错: %s", e)

        log.info("结束")
    

if __name__ == "__main__":
    main()
