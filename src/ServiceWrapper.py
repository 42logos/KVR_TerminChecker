import subprocess
import sys

import win32serviceutil
import win32service
import win32event
import servicemanager
import Main
import traceback
import logging
import os


class ServiceWrapper(win32serviceutil.ServiceFramework):
    _svc_name_ = "AppointmentCheckerService"
    _svc_display_name_ = "AppointmentCheckerService"
    _svc_description_ = "Service for checking appointments at the Munich registration office."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        log_file_path = os.path.join(os.path.dirname(__file__), f'{self._svc_name_}_service.log')
        self.logger = logging.getLogger(self._svc_name_)
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.logger.info("Service is stopping.")

    def SvcDoRun(self):
        self.logger.info("Service is starting.")
        try:
            self.main()
        except Exception as e:
            self.logger.error(f"Error in SvcDoRun: {str(e)}")
            self.logger.error(traceback.format_exc())

    def main(self):

        subprocess.check_call([sys.executable, "-m","Main"])


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ServiceWrapper)
