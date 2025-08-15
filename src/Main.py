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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
    WebDriverException,
    InvalidArgumentException
)
from selenium.webdriver.support import expected_conditions as EC

from tqdm import tqdm
import time
import os
import sys

from loguru import logger
import random

import threading
logger.remove()  # 移除默认的日志处理器
sys.stdout.reconfigure(encoding='utf-8')  # 设置标准输出编码为 utf-8

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

import sys,pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent.resolve()))  # 添加 src 目录到 sys.path
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
    "KontaktClick": settings.default.KontaktClick,
    "Appointment_idx": settings.default.Appointment_idx,
    "proxy": settings.default.PROXY,
    
}
logger.info("当前配置: {}", config)
# ─────────────────────────────────────


# ─────────── 工具：获取 shadowRoot ───────────
def get_shadow_element(driver, selector: str, inner_css: str, timeout: int = TIMEOUT):
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
    try:
        element = wait.until(lambda d: root.find_elements(selector, inner_css))
    except InvalidArgumentException:
        # 可能是因为没有找到元素，导致 InvalidArgumentException
        logger.info("  选择器无效: {}", selector)
        raise InvalidArgumentException(f"选择器无效: {selector}")
    logger.debug("  找到元素: {}", inner_css)
    # 4️⃣ 滚动到可见位置
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", element[0]) # 滚动到可见位置
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
    # insert current full config to filename
    filename = filename.replace(".html", f"_{settings.default.SERVICE_ID}_{settings.default.LOCATION_ID}_{settings.default.Appointment_idx}.html")


    # 2) 保存到文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write(shadow_html)
    logger.debug("  保存当前页面源代码到: {}", filename)

# ─────────── 工具: 处理具体时间 ───────────
def select_appointment(driver, idx: int = 0, timeout: int = TIMEOUT):
    """
    点击具体的预约时间按钮"""
    #driver.get("http://127.0.0.1:5500/page_source_8_ac.html") # 模拟加载本地文件
    
    # 2) 再抓一次列表（避免 stale）
    slots = get_shadow_element(driver, By.CSS_SELECTOR, inner_css="div.select-appointment")
    
    #列出所有时间按钮
    logger.info("  可用时间:")
    slottexts=[slot.text.strip() for slot in slots]
    logger.info("  {}", slottexts)

    # 3) 找到目标元素
    if not idx==-1:
        if idx>=len(slots):
            raise RuntimeError(f"索引超出范围: {idx} > {len(slots)}")
        target = slots[idx]  # 直接使用索引获取目标元素
        save_page_source(driver, f"page_source_{target.text.strip()}.html")  # 保存当前页面源代码
        safe_click(driver, target, target.text.strip(), timeout=timeout)
    else:
        logger.info("选择所有时间按钮")
        for slot in slots:
           safe_click(driver, slot, slot.text.strip(), timeout=timeout)
        logger.info("已成功点击所有时间按钮")


#─────────── 工具: 点击Kontaktdatenangeben ───────────
def click_kontakt(driver, timeout=TIMEOUT):
    """点击『Kontaktdaten angeben』按钮"""
    # 1) 等待按钮加载完成
    element= get_shadow_element(driver, By.CSS_SELECTOR, inner_css="button.v-expansion-panel-header")[0]  # 只取第一个元素
    
    safe_click(driver, element, "Kontaktdaten angeben", timeout=timeout)
    logger.info("已成功点击『Kontaktdaten angeben』按钮")
        
    
# ─────────── 工具：安全点击元素 ───────────
def safe_click(driver, element, time_str, timeout=TIMEOUT):
    """滚动到 element 并尝试点击，失败时降级到 JS 点击"""

    try:
        ActionChains(driver).move_to_element(element).perform()
        html = element.get_attribute("outerHTML")  # 这里可能会抛异常
    except StaleElementReferenceException:
        logger.warning("元素已失效，尝试重新获取...")
        # 重新获取 shadow DOM 中的所有按钮
        elements = get_shadow_element(driver, By.CSS_SELECTOR, "div.select-appointment")
        element = next((el for el in elements if el.text.strip() == time_str), None)
        if not element:
            raise RuntimeError(f"重新获取元素失败：{time_str}")
        html = element.get_attribute("outerHTML")

    logger.info("  滚动到元素: {}", html)

    # 确保元素可见 & 可点击
    WebDriverWait(driver, timeout).until(
        lambda d: element.is_displayed() and element.is_enabled()
    )

    # 2) 尝试原生 click
    try:
        element.click()
    except (ElementClickInterceptedException,
            ElementNotInteractableException,
            WebDriverException) as e:
        print(f"原生 click 失败 → {e.__class__.__name__}: {e.msg.splitlines()[0]}")
        try:
            driver.execute_script("arguments[0].click();", element)
        except StaleElementReferenceException:
            raise RuntimeError("元素再次失效，点击失败")

    print(f"已成功点击 {time_str}")

def js_click(driver, element):
    """使用 JS 点击元素"""
    try:
        driver.execute_script("arguments[0].click();", element)
    except StaleElementReferenceException:
        raise RuntimeError("元素失效，点击失败")
    logger.info("  使用 JS 点击元素: {}", element.get_attribute("outerHTML"))
    # 3) 等待弹窗出现

# ─────────── 打开浏览器 ───────────
def open_browser():
    
    #checking if chrome is installed

    
    
    opts = webdriver.ChromeOptions()
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_argument("--no-sandbox")                     # 解决 DevToolsActivePort 文件不存在的报错
    opts.add_argument("--disable-dev-shm-usage") # 解决 DevToolsActivePort 文件不存在的报错
    opts.add_argument("--headless") if settings.default.HEADLESS else None  # 无头模式
    opts.add_argument("--disable-gpu") if settings.default.HEADLESS else None  # 无头模式
    #opts.add_argument("--remote-debugging-port=9222") # 远程调试端口
    opts.add_argument("--proxy-server=127.0.0.1:8080") if settings.default.PROXY else None  # 代理服务器
    opts.add_argument("--ignore-certificate-errors")  # 允许忽略证书错误
    opts.add_argument("--disable-blink-features=AutomationControlled") # 禁用自动化提示
    

    service = Service(ChromeDriverManager().install(), log_level="INFO")
    return webdriver.Chrome(service=service, options=opts)


# ───────────  单次检查 ───────────
def check_once(driver, date: str):
    url = (
        "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/10339027/locations/10187259"
    )
    logger.debug("打开页面: {}", url)
    driver.get(url)
    
    # 1) 尝试点击captcha checkbox
    captch_css="div.altcha-checkbox"
    try:
        captcha = get_shadow_element(driver, By.CSS_SELECTOR, inner_css=captch_css, timeout=3)[0]  # 只取第一个元素
        logger.info("尝试点击验证码复选框 …")
        time.sleep(random.uniform(0.5, 1.5))  # 等待一段时间，模拟人类操作
        captcha.click()
        logger.info("点击成功")
    except NoSuchElementException:
        logger.info("验证码复选框未找到，跳过")
    except TimeoutException:
        logger.info("验证码复选框加载超时，跳过")

    # 2) 点击『Weiter zur Terminsuche』/ 下一步
    logger.info("尝试点击『Weiter / Nächster Schritt』按钮 …")
    next_btn = get_shadow_element(
        driver,
        By.CSS_SELECTOR,
        inner_css="button.button-next",
    )[0]  # 只取第一个元素
    safe_click(driver, next_btn, "Weiter / Nächster Schritt", timeout=TIMEOUT)
    logger.info("点击成功")
    # 3) 读取日历：所有可用日期按钮带 data-date 属性且未 disabled


    # 日历组件 <zms-calendar> 也在 Shadow DOM
    logger.info("尝试加载日历组件 …")
    # driver.get("E:\Programming_Projects\KVR_TerminChecker\page_source_7.html") # 模拟加载本地文件
    calendar = get_shadow_element(
        driver,
        By.CSS_SELECTOR,
        inner_css="table",           # 只为了拿到 shadowRoot
    )[0]  # 只取第一个元素
    # calendar = driver.find_element(By.CSS_SELECTOR, "table")
    # save_page_source(driver, "page_source_calendar.html")
    logger.info("日历组件已加载")
    
    logger.info("尝试分析日历 …")
    available_dates = []

    for day in range(1, 32):
        if is_day_enabled(calendar, day):
            alert_thread = threading.Thread(target=alert_sound)
            alert_thread.start()
            
            logger.info("日期 {} 可用", day)
            available_dates.append(day)
            
            ## 4) 点击日期按钮
            click_day(calendar, day)
            # save_page_source(driver, f"page_source_{day}_clicked.html")
            
    
            
            # 5) 点击时间按钮
            select_appointment(driver, idx=settings.default.Appointment_idx, timeout=TIMEOUT) 
            save_page_source(driver, f"page_source_{day}_clicked_time.html")
            
            # 6) 点击『Kontaktdaten angeben』按钮
            click_kontakt(driver, timeout=TIMEOUT) if settings.default.KontaktClick else None
            save_page_source(driver, f"page_source_{day}_clicked_kontakt.html") if settings.default.KontaktClick else None
            
            
            while True:
                pass
    logger.info("本月可预约日期: {}", ", ".join(map(str, available_dates)) or "— 无 —")
        



# ─────────── 主流程 ───────────
from utils import is_available
def main():
    logger.info("开始检查 …")
    refresh_interval = 0.5
    while not is_available():
        logger.info(f"预约系统不可用，等待 {refresh_interval} 秒后重试 …")
        time.sleep(random.uniform(refresh_interval * 0.7, refresh_interval * 1.3))  # 等待一段时间后重试
    logger.info("预约系统可用，开始检查可预约日期 …")
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
            try:
                logger.exception("执行过程中出错: {}", e)
                logger.info("等待 {} 秒后重启 …", RESTART_INTERVAL)
                # 等待一段时间后重启浏览器
                for _ in tqdm(range(int(RESTART_INTERVAL)*10), desc="等待中",ncols=80, bar_format="{l_bar}{bar}| [{elapsed}<{remaining}]"):
                    time.sleep(RESTART_INTERVAL / 150)
                # 休息完了，重启浏览器
                driver.quit()
                try:
                    pass
                    #os.system("taskkill /f /im chrome.exe")
                except Exception as e:
                    logger.exception("强制关闭浏览器失败: {}", e)
                # 重新打开浏览器
                driver = open_browser()
                logger.info("重启浏览器 …")
            except KeyboardInterrupt:
                logger.info("检测到手动中断，退出 …")
                break
            except Exception as e:
                logger.exception("重启浏览器失败: {}", e)
                logger.info("尝试强制关闭浏览器 …")

                os.system("taskkill /f /im chrome.exe")
        finally:
            logger.info("结束")
    

    logger.info("强制关闭浏览器")
    #强制关闭浏览器
    os.system("taskkill /f /im chrome.exe")
    logger.info("结束")
    logger.info("程序已完成")


if __name__ == "__main__":
    main()