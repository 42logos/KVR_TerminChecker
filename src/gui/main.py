import ctypes
import os
import sys
from threading import Thread

import dearpygui.dearpygui as dpg
import io

dpg.create_context()

T=None


class OutputRedirector(io.StringIO):
    def __init__(self, tag, parent_tag, line_length=80):
        super().__init__()
        self.tag = tag
        self.parent_tag = parent_tag
        self.line_length = line_length

    def write(self, s):
        super().write(s)
        current_value = dpg.get_value(self.tag)
        dpg.set_value(self.tag, current_value + s)

        # 滚动到子窗口底部
        dpg.set_y_scroll(self.parent_tag, dpg.get_y_scroll_max(self.parent_tag))


def _async_raise(tid, exctype):
    if not isinstance(exctype, type):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("Invalid thread id")
    elif res != 1:
        # if it returns a number greater than one, we're in trouble, and we should call it again with exc=0 to revert the effect
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")

def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def button1_callback(sender, app_data):

    print("TerminChecker started.")

    os.environ['CHECK_INTERVAL'] = str(dpg.get_value('df'))
    os.environ['RESTART_INTERVAL'] = str(dpg.get_value('RestartInterval'))
    os.environ['HEADLESS'] = str(dpg.get_value('headless'))
    print(f"Check Interval: {os.environ['CHECK_INTERVAL']}"
          f"\nRestart Interval: {os.environ['RESTART_INTERVAL']}"
          f"\nHeadless: {os.environ['HEADLESS']}")
    import logik as Main
    import importlib
    importlib.reload(Main)
    global T
    T = Thread(target=Main.main,daemon=True)
    T.start()
def button2_callback(sender, app_data):
    global T

    stop_thread(T)

    print(f'Thread {T.ident} is { "alive" if T.is_alive() else "dead"}')
    T = None


with dpg.window(label="TerminChecker", tag='primary_window', no_resize=True, no_move=True, no_close=True):
    with dpg.child_window(label="IntervalWindow", pos=(10, 20), width=300, height=100):
        dpg.add_text("Check Interval:")
        dpg.add_slider_int(tag='df', width=150, pos=(135, 10), default_value=5, min_value=0, max_value=60, clamped=True,
                           vertical=False)
        dpg.add_text("Restart Interval:", pos=(8, 40))

        dpg.add_slider_int(tag='RestartInterval', width=150, pos=(135, 40), default_value=5, min_value=1, max_value=60,
                           clamped=True, vertical=False)
        dpg.add_checkbox(label='headless', tag='headless', pos=(10, 70),default_value=True)
    dpg.add_button(label="Start", callback=button1_callback, tag='button1', width=100, pos=(50, 150))
    dpg.add_button(label="Stop", callback=button2_callback, tag='button2', width=100, pos=(175, 150))
    with dpg.child_window(label="LogWindow", tag="LogWindow", pos=(10, 190), width=300, height=270,horizontal_scrollbar=True):
        dpg.add_text("Log:")
        dpg.add_text("", tag="LogText")  # 添加用于显示日志内容的文本标签

# 重定向标准输出到日志窗口
sys.stdout = OutputRedirector(tag="LogText", parent_tag="LogWindow", line_length=50)  # 设置自动换行长度

dpg.create_viewport(title='TerminChecker', width=340, height=520, resizable=False)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window('primary_window', True)
dpg.set_exit_callback(lambda: stop_thread(T) if T else None)
# 启动后台任务线程


dpg.start_dearpygui()


dpg.destroy_context()
