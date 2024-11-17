from upbit.upbit_trading import *
from common_Import import *

class Ui_class():
    def __init__(self):
        # print("Ui_class 입니다\n")
        
        self.app = QApplication(sys.argv) # QApplication는 빈 깡통 상태의 어플 Ui
        
        self.upbit = Upbit_trading_system()
        
        self.app.exec_() # 프로그램이 계속 돌아가기 위해서 해당 코드를 통해 py파일이 종료되지 않도록 해주는 코드