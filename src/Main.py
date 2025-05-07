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
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from tqdm import tqdm
import time
import os
import sys

from loguru import logger
import random

import threading
logger.remove()  # 移除默认的日志处理器
sys.out.reconfigure(encoding='utf-8')  # 设置输出编码为 utf-8

logger.add(
    sink="logs/{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="1 day",
    retention="7 days",
    compression="zip",

)
logger.add(
        sink=sys.stdout,
        level="INFO",
    
    )

logger.debug("Logger initialized with name: Main")

#设置tqdm的进度条格式


from config import settings
# ─────────────── 配 置 ───────────────
SERVICE_ID = settings.default.SERVICE_ID  if settings.default.SERVICE_ID else "10339027"  # 
LOCATION_ID = settings.default.LOCATION_ID if settings.default.LOCATION_ID else "10187259"  
TARGET_DATE = time.strftime("%Y-%m-%d", time.localtime())  # 今天的日期
TIMEOUT     = settings.default.TIMEOUT     if settings.default.TIMEOUT     else 10  # 等待时间
BREAK_INTERVAL = settings.default.BREAK_INTERVAL if settings.default.BREAK_INTERVAL else 5  # 检查间隔秒数
RESTART_INTERVAL = settings.default.RESTART_INTERVAL if settings.default.RESTART_INTERVAL else 35  # 重启间隔秒数
HEADLESS = settings.default.HEADLESS if settings.default.HEADLESS else False  # 是否无头模式
config = {
    "SERVICE_ID": SERVICE_ID,
    "LOCATION_ID": LOCATION_ID,
    "TARGET_DATE": TARGET_DATE,
    "TIMEOUT": TIMEOUT,
    "BREAK_INTERVAL": BREAK_INTERVAL,
    "RESTART_INTERVAL": RESTART_INTERVAL,
    "HEADLESS": HEADLESS,
    
}
logger.info("当前配置: {}", config)
# ─────────────────────────────────────


# ─────────── 工具：获取 shadowRoot ───────────
def get_shadow_element(driver, inner_css: str, timeout: int = TIMEOUT):
    """在 WebComponent 的 shadowRoot 内查找元素"""
    wait = WebDriverWait(driver, timeout)

    # 1️⃣ 等待 host 元素加载完成
    host = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "zms-appointment")))
    logger.debug("  zms-appointment 已加载")

    # 2️⃣ 等待 shadowRoot 加载完成
    def shadow_root_ready(driver):
        try:
            root = host.shadow_root
            return root
        except Exception:
            return False

    root = wait.until(shadow_root_ready)
    logger.debug("  shadowRoot 已加载")
    
    # 3️⃣ 再等element真正出现在 root 里
    element = wait.until(lambda d: root.find_element(By.CSS_SELECTOR, inner_css))
    logger.debug("  找到元素: {}", inner_css)
    # 4️⃣ 滚动到可见位置
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", element) # 滚动到可见位置
    logger.debug("  滚动到可见位置")
    # 5️⃣ 返回元素
    return element

# ─────────── 工具：判断日期按钮是否可用 ───────────
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
    logger.debug("  日期 {} 可用: {}", day, btn.is_enabled())
    return btn.is_enabled()

# ─────────── 工具：播放警告 ───────────
def alert_sound():
    """播放警告音效"""
    import winsound
    frequency = 440  # Set Frequency To 440 Hertz
    duration = 1000  # Set Duration To 1000 ms == 1 second
    while True:
        winsound.Beep(frequency, duration)

# ─────────── 工具：点击日期按钮 ───────────
def click_day(table, day: int):
    """
    在已定位到的日历 shadow_root（或 container）中，
    查找日期为 day 的按钮并点击它。
    """
    logger.info("  尝试点击日期: {}", day)
    # 1) 用 XPath 找到包含数字的 <div>，然后拿它的父 <button>
    btn = table.find_element(
        By.XPATH,
        f".//button[.//div[text()='{day}']]"
    )
    # 2) 点击按钮
    btn.click()
    logger.info("  点击日期 {} 成功", day)
    # 3) 等待弹窗出现

# ─────────── 工具：保存当前完整网页源代码 以供分析 ───────────
def save_page_source(driver, filename: str):
    """""保存当前完整网页源代码 以供分析"""
    # 1) 获取 shadowRoot 的完整 HTML 源代码
    shadow_html = driver.execute_script(
    "return arguments[0].shadowRoot.innerHTML", 
        driver.find_element(By.CSS_SELECTOR, "zms-appointment")
    )

    # 2) 保存到文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(shadow_html)
    logger.debug("  保存当前页面源代码到: {}", filename)


# ─────────── 打开浏览器 ───────────
def open_browser():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--log-level=3")                          # 静音 USB 报警
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_argument("--disable-infobars")                  # 隐藏提示条
    opts.add_argument("--disable-extensions")                # 禁用扩展
    opts.add_argument("--disable-popup-blocking")            # 禁用弹窗拦截
    opts.add_argument("--no-sandbox")                     # 解决 DevToolsActivePort 文件不存在的报错
    opts.add_argument("--disable-dev-shm-usage") # 解决 DevToolsActivePort 文件不存在的报错
    opts.add_argument("--headless") if settings.default.HEADLESS else None  # 无头模式
    opts.add_argument("--disable-gpu") if settings.default.HEADLESS else None  # 无头模式
    opts.add_argument("--user-data-dir=C:/Temp/ChromeProfile")

    service = Service(ChromeDriverManager().install(), log_level="INFO")
    return webdriver.Chrome(service=service, options=opts)


# ───────────  单次检查 ───────────
def check_once(driver, date: str):
    url = (
        "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/10339027/locations/10187259"
    )
    logger.debug("打开页面: {}", url)
    driver.get(url)

    try:

        # 2) 点击『Weiter zur Terminsuche』/ 下一步
        logger.info("尝试点击『Weiter / Nächster Schritt』按钮 …")
        next_btn = get_shadow_element(
            driver,
            inner_css="button.m-button.m-button--primary.m-button--animated-right.button-next",
        )
        next_btn.click()
        logger.info("点击成功")
        # 3) 读取日历：所有可用日期按钮带 data-date 属性且未 disabled


        # 日历组件 <zms-calendar> 也在 Shadow DOM
        logger.info("尝试加载日历组件 …")
        # driver.get("E:\Programming_Projects\KVR_TerminChecker\page_source_7.html") # 模拟加载本地文件
        calendar = get_shadow_element(
            driver,
            inner_css="table",           # 只为了拿到 shadowRoot
        )
        # calendar = driver.find_element(By.CSS_SELECTOR, "table")
        save_page_source(driver, "page_source_calendar.html")
        logger.info("日历组件已加载")
        
        logger.info("尝试分析日历 …")
        available_dates = []
    
        for day in range(1, 32):
            if is_day_enabled(calendar, day):
                logger.info("日期 {} 可用", day)
                save_page_source(driver, f"page_source_{day}.html")  
                available_dates.append(day)
                click_day(calendar, day)
                save_page_source(driver, f"page_source_{day}_clicked.html")
                # 点击日期按钮后，可能会弹出一个确认框
                alert_sound()
        logger.info("本月可预约日期: {}", ", ".join(map(str, available_dates)) or "— 无 —")
        

    except Exception as e:
        logger.exception("执行过程中出错: {}", e)
    finally:
        logger.debug("结束")


# ─────────── 主流程 ───────────

def main():
    logger.info("开始检查 …")
    driver = open_browser()
    while True:
        try:
                driver.refresh()
                logger.info("检查可预约日期 …")
                check_once(driver, TARGET_DATE)

                # 等待一段时间后再检查
                
                real_break_interval = BREAK_INTERVAL * random.uniform(0.7, 1.8)
                logger.info("等待 {} 秒后继续 …", real_break_interval.__round__(2))
                
                # 等待一段时间后再检查
                for _ in tqdm(range(int(10 * real_break_interval)), desc="等待中",ncols=80, bar_format="{l_bar}{bar}| [{elapsed}<{remaining}]"):
                    time.sleep(real_break_interval / 75)
                # 休息完了，刷新页面
                driver.refresh()
                logger.info("刷新页面 …")
        except KeyboardInterrupt:
            logger.info("检测到手动中断，退出 …")
            break
        except Exception as e:
            logger.exception("执行过程中出错: {}", e)
            logger.info("等待 {} 秒后重启 …", RESTART_INTERVAL)
            # 等待一段时间后重启浏览器
            for _ in tqdm(range(int(RESTART_INTERVAL)*10), desc="等待中",ncols=80, bar_format="{l_bar}{bar}| [{elapsed}<{remaining}]"):
                time.sleep(RESTART_INTERVAL / 150)
            # 休息完了，重启浏览器
            driver.quit()
            driver = open_browser()
            logger.info("重启浏览器 …")

        logger.info("结束")

    logger.info("强制关闭浏览器")
    #强制关闭浏览器
    os.system("taskkill /f /im chrome.exe")
    logger.info("结束")
    logger.info("程序已完成")


if __name__ == "__main__":
    main()