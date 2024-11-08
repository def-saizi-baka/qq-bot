from poe_api_wrapper import AsyncPoeApi

class PoeBot():
    def __init__(self, max_lock = 10) -> None:
        self.lock_cnt = 0; # 记录使用数量
        self.max_lock = max_lock; # 最大使用数量
        self.client = None
    
    async def init(self, tokens):
        proxy = ["socks5://127.0.0.1:7890"]
        self.client = await AsyncPoeApi(tokens=tokens, proxy=proxy).create()
    
    # 简单的锁机制
    def on_lock(self):
        self.lock_cnt += 1
    
    def on_unlock(self):
        self.lock_cnt -= 1
    
    def is_locked(self):
        return self.lock_cnt >= self.max_lock
        
    
    