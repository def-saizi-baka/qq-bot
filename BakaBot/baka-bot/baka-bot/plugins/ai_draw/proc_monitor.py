from typing import Tuple
import psutil
import time
from .config import DrawBotConfig

class ProcMonitor():
    def __init__(self, botCfg: DrawBotConfig):
        self.botCfg = botCfg
        # ComfyUI进程的参数关键词, 用于检测是否已经启动 + 关闭
        self.ai_cmd_key = botCfg.ai_cmd_key
        # 游戏进程定义
        self.game_proc_dict = botCfg.game_proc_dict
        self.notice_time = 0

    # 检查AI绘画进程是否正在运行
    def is_ai_drawing_running(self):
        for proc in psutil.process_iter(['name']):
            if 'python.exe' in proc.info['name']:
                for arg in proc.cmdline():
                    if self.ai_cmd_key in arg:
                        return True
        return False
    
    # 检查游戏进程是否正在运行
    def is_game_running(self) -> Tuple[bool, str]:
        exec_names = self.game_proc_dict.keys()
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in exec_names:
                return True, self.game_proc_dict[proc.info['name']]
        return False, ""

    # 关闭AI绘画进程
    def close_ai_drawing(self):
        for proc in psutil.process_iter(['name']):
            if 'python.exe' in proc.info['name']:
                for arg in proc.cmdline():
                    if self.ai_cmd_key in arg:
                        proc.terminate()
                        print("已关闭AI绘画进程")
                        break
    
    def get_notice_time(self) -> int:
        return self.notice_time
    
    # 设置下一次更新时间 (+60s) (用于控制通知频率)
    def update_notice_time(self):
        self.notice_time = int(time.time()) + 60