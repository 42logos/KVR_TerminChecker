import builtins
import io
import logging
import pytest

import appointment_checker


class DummyDriver:
    def __init__(self, script_return=None, page_source="<html></html>"):
        self._script_return = script_return
        self.page_source = page_source
        self.get_calls = []

    def execute_script(self, script):
        return self._script_return

    def get(self, url):
        self.get_calls.append(url)


def test_get_appointments_via_js_returns_data():
    data = {"LOADBALANCER": {"appoints": {"1": [1, 2]}}}
    driver = DummyDriver(script_return=data)
    result = appointment_checker._get_appointments_via_js(driver)
    assert result == data


def test_get_appointments_via_js_returns_none():
    driver = DummyDriver(script_return=None)
    result = appointment_checker._get_appointments_via_js(driver)
    assert result is None


@pytest.mark.parametrize("return_value, expected", [
    (True, True),
    (False, False),
])
def test_no_appointments_callout(monkeypatch, return_value, expected):
    driver = DummyDriver(script_return=return_value)
    assert appointment_checker._no_appointments_callout(driver) is expected


def test_setup_driver_monkeypatched(monkeypatch):
    # 模拟 webdriver.Chrome 和 ChromeOptions
    class FakeOptions:
        def __init__(self):
            self.args = []

        def add_argument(self, arg):
            self.args.append(arg)

    class FakeChrome:
        def __init__(self, options):
            self.options = options

    monkeypatch.setattr(appointment_checker.webdriver, "ChromeOptions", FakeOptions)
    monkeypatch.setattr(appointment_checker.webdriver, "Chrome", FakeChrome)

    driver = appointment_checker.setup_driver()
    # 返回的 driver 应该是我们 FakeChrome 的实例，且带有 options
    assert isinstance(driver, FakeChrome)
    assert isinstance(driver.options, FakeOptions)
    # 确保一些常用的参数被添加
    assert "--disable-gpu" in driver.options.args
    assert "--no-sandbox" in driver.options.args


def test_configure_logging_creates_handlers(monkeypatch):
    # 清空已有 handlers
    logger = logging.getLogger("app_logger")
    logger.handlers.clear()

    appointment_checker.configure_logging()

    handlers = logger.handlers
    # 至少一个 RotatingFileHandler 和 一个 StreamHandler
    types = {type(h) for h in handlers}
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in handlers)
    assert any(isinstance(h, logging.StreamHandler) for h in handlers)
    # 日志级别
    fh = next(h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler))
    ch = next(h for h in handlers if isinstance(h, logging.StreamHandler))
    assert fh.level == logging.DEBUG
    assert ch.level == logging.INFO


def test_check_appointments_timeout(monkeypatch):
    # 1) 不实际打开页面
    monkeypatch.setattr(appointment_checker, "load_appointment_page", lambda drv: None)
    # 2) 永远没有 JSON，也没有 callout
    monkeypatch.setattr(appointment_checker, "_get_appointments_via_js", lambda drv: None)
    monkeypatch.setattr(appointment_checker, "_no_appointments_callout", lambda drv: False)
    # 3) 强制 WAIT_TIMEOUT=0，使 while 不执行
    monkeypatch.setattr(appointment_checker, "WAIT_TIMEOUT", 0)

    drv = DummyDriver()
    result = appointment_checker.check_appointments(drv)
    assert result is False


def test_check_appointments_finds_slot(monkeypatch, tmp_path):
    # 准备一个能返回非空 slot 的 JSON
    slot_data = {"LOADBALANCER": {"appoints": {"slot1": [ {"foo": "bar"} ]}}}
    monkeypatch.setattr(appointment_checker, "load_appointment_page", lambda drv: None)
    monkeypatch.setattr(appointment_checker, "_get_appointments_via_js", lambda drv: slot_data)
    # callout 不会被调用到
    monkeypatch.setattr(appointment_checker, "_no_appointments_callout", lambda drv: False)
    # 确保不会真的无限响铃
    called = {"alert": False}
    monkeypatch.setattr(appointment_checker, "play_alert_sound", lambda: called.update(alert=True))
    # 拦截 open 写文件
    dummy_file = io.StringIO()
    def fake_open(path, mode='r', encoding=None):
        assert path == "source.html"
        return dummy_file
    monkeypatch.setattr(builtins, "open", fake_open)

    drv = DummyDriver(page_source="<p>PAGE</p>")
    # 运行；应当返回 True
    result = appointment_checker.check_appointments(drv)
    assert result is True
    # 确保 play_alert_sound 被调用
    assert called["alert"] is True
    # 确保 page_source 被写入
    assert "<p>PAGE</p>" in dummy_file.getvalue()
