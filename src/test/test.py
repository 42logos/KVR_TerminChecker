import importlib
import unittest
from unittest.mock import patch, MagicMock
import os
import logging
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver

# 导入被测试的模块
import Main


class TestAppointmentChecker(unittest.TestCase):
    @patch('dotenv.load_dotenv')
    def test_load_env(self, mock_load_dotenv):
        # 重新加载 Main 模块以捕获 load_dotenv 调用
        import importlib
        importlib.reload(Main)
        mock_load_dotenv.assert_called_once()

    @patch.dict(os.environ,
                {'APPOINTMENT_URL':'test_url', 'CHECK_INTERVAL': '20', 'RESTART_INTERVAL': '60', 'WAIT_TIMEOUT': '10'})
    def test_read_env_variables(self):
        import Main
        importlib.reload(Main)




        from Main import APPOINTMENT_URL, CHECK_INTERVAL, RESTART_INTERVAL, WAIT_TIMEOUT

        self.assertEqual(APPOINTMENT_URL, 'test_url')
        self.assertEqual(CHECK_INTERVAL, 20)
        self.assertEqual(RESTART_INTERVAL, 60)
        self.assertEqual(WAIT_TIMEOUT, 10)

    @patch('logging.getLogger')
    @patch('logging.StreamHandler', side_effect=logging.StreamHandler)
    @patch('logging.Formatter')
    @patch('logging.handlers.RotatingFileHandler')
    def test_configure_logging(self, mock_rotating_file_handler, mock_formatter, mock_stream_handler, mock_get_logger):
        Main.configure_logging()
        mock_get_logger.assert_any_call('app_logger')
        mock_get_logger.assert_any_call('selenium.webdriver.remote.remote_connection')
        mock_get_logger.assert_any_call('urllib3.connectionpool')
        mock_rotating_file_handler.assert_called()
        mock_formatter.assert_called()
        mock_stream_handler.assert_called()




    @patch('selenium.webdriver.Chrome')
    def test_setup_driver(self, mock_chrome):
        from Main import setup_driver
        driver = setup_driver()
        mock_chrome.assert_called()

    @patch.object(WebDriverWait, 'until')
    @patch.object(WebDriver, 'get')
    def test_load_appointment_page(self, mock_get, mock_until):
        from Main import load_appointment_page
        APPOINTMENT_URL = 'https://terminvereinbarung.muenchen.de/abh/termin/?cts=1000113'
        mock_driver = MagicMock(spec=WebDriver)
        mock_select_element = MagicMock()
        mock_select_element.tag_name = 'select'
        mock_until.return_value = mock_select_element
        load_appointment_page(mock_driver)
        mock_driver.get.assert_called_with(APPOINTMENT_URL)
        mock_until.assert_called()

    @patch.object(WebDriverWait, 'until')
    @patch.object(Select, 'select_by_value')
    @patch.object(WebDriver, 'find_element')
    def test_select_appointment_type(self, mock_find_element, mock_select_by_value, mock_until):
        from Main import select_appointment_type
        mock_driver = MagicMock(spec=WebDriver)
        mock_element = MagicMock()
        mock_element.tag_name = 'select'
        mock_until.return_value = MagicMock()
        select_appointment_type(mock_driver, mock_element)
        mock_select_by_value.assert_called_with('1')
        mock_until.assert_called()

    @patch.object(WebDriver, 'find_elements')
    def test_extract_json_data(self, mock_find_elements):
        from Main import extract_json_data
        mock_driver = MagicMock(spec=WebDriver)

        # Create multiple mock script elements
        mock_script_1 = MagicMock()
        mock_script_1.get_attribute.return_value = 'some other script content'

        mock_script_2 = MagicMock()
        mock_script_2.get_attribute.return_value = 'var jsonAppoints = {"LOADBALANCER": {"appoints": {"1": "data"}}};'

        mock_find_elements.return_value = [mock_script_1, mock_script_2]

        # Set mock driver to return the mock scripts
        mock_driver.find_elements.return_value = mock_find_elements.return_value

        # Print the mock elements to verify
        scripts = mock_driver.find_elements(By.TAG_NAME, 'script')
        print(f"Scripts found: {[script.get_attribute('innerHTML') for script in scripts]}")

        json_data = extract_json_data(mock_driver)
        self.assertEqual(json_data, {"LOADBALANCER": {"appoints": {"1": "data"}}})

    @patch('logging.getLogger')
    @patch('Main.play_alert_sound')
    @patch.object(WebDriver, 'page_source', new_callable=MagicMock)
    @patch.object(WebDriver, 'find_elements')
    @patch.object(WebDriverWait, 'until')
    @patch.object(WebDriver, 'get')
    def test_check_appointments(self, mock_get, mock_until, mock_find_elements, mock_page_source, mock_play_alert_sound,
                                mock_get_logger):
        from Main import check_appointments
        mock_driver = MagicMock(spec=WebDriver)
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Mocking the <select> element
        mock_element = MagicMock()
        mock_element.tag_name = 'select'

        # Set required methods and attributes for the select element
        mock_option = MagicMock()
        mock_option.get_attribute.return_value = '1'
        mock_element.find_elements.return_value = [mock_option]

        mock_until.side_effect = [mock_element, MagicMock()]



        # Mocking the <script> elements
        mock_script_1 = MagicMock()
        mock_script_1.get_attribute.return_value = 'some other script content'

        mock_script_2 = MagicMock()
        mock_script_2.get_attribute.return_value = 'var jsonAppoints = {"LOADBALANCER": {"appoints": {"1": ["some_appointment_data"]}}};'

        mock_find_elements.return_value = [mock_script_1, mock_script_2]

        # Set mock driver to return the mock scripts
        mock_driver.find_elements.return_value = mock_find_elements.return_value
        mock_driver.page_source = '<html><body>Mock page source with appointment data</body></html>'

        # Print the mock elements to verify
        scripts = mock_driver.find_elements(By.TAG_NAME, 'script')
        print(f"Scripts found: {[script.get_attribute('innerHTML') for script in scripts]}")

        available = check_appointments(mock_driver)
        self.assertTrue(available)
        mock_play_alert_sound.assert_called()
        mock_logger.info.assert_called()


if __name__ == "__main__":
    unittest.main()
