from poe_api_wrapper import AsyncPoeApi
import json

class PoeBot():
    def __init__(self) -> None:
        # 锁配置
        self.lock_cnt = 0; # 记录使用数量
        self.max_lock = 0; # 最大使用数量
        self.client = None
        self.config = {}
    
    async def init(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        tokens = self.config['tokens']
        proxy = self.config['proxys']
        self.max_lock = self.config['max_lock']
        self.client = await AsyncPoeApi(tokens=tokens, proxy=proxy).create()
    
    # 简单的锁机制
    def on_lock(self):
        self.lock_cnt += 1
    
    def on_unlock(self):
        self.lock_cnt -= 1
    
    def is_locked(self):
        return self.lock_cnt >= self.max_lock
        
    
    