from pydantic import BaseModel
import json, os, time

class Config(BaseModel):
    """Plugin Config Here"""
    HISTORY_SESSION_INTERVAL: int = 60  # 会话记录保存间隔
    ALLOWED_GROUPS: list = [             # 允许使用的群组
            '3281272972', '206424201', '499651782', '825693798'
        ]
    # 触发概率配置
    TRIGGER_CFG: dict = {
        '3281272972': 1,
        '206424201': 0.2,
        '499651782': 0.2,
        '825693798': 0.2
    }


class BotConfig():
    def __init__(self, config_path):
        self.config_path = config_path
        self.bot_map = {}
        self.read_config()
        self.mute_map = {
            '3281272972': 0,
            '206424201': 0,
            '499651782': 0,
            '825693798': 0
        }

    def read_config(self):
        ''' Read config from file '''
        print(f'Config Path: {self.config_path}')
        with open(self.config_path, 'r') as file:
            self.bot_map = json.load(file)
        print(f'bot_map: {self.bot_map}')
    
    def save_config(self):
        ''' Save config to file '''
        with open(self.config_path, 'w') as file:
            json.dump(self.bot_map, file)
    
    def get_select_msg(self):
        ''' Get select message '''
        bot_temp_map = self.bot_map['99999']
        msg = f'请选择模型序号 [0 ~ {len(bot_temp_map.keys())-1}]:\n'
        no = 0
        for key in bot_temp_map:
            bot_cfg = bot_temp_map[key]
            msg += f' {no}. {bot_cfg["bot_name"]}'
            # is_selected = bot_cfg.get('selected', {}).get(str(owner_no), False)
            # if (is_selected):
            #     msg += ' (当前选择) '
            msg += '\n'
            no += 1
        return msg

    def select_bot(self, owner_no: int, select_no):
        ''' Select bot by no '''
        owner_no = str(owner_no)
        # 当前群组的bot
        group_bot_map = self.bot_map[owner_no]
        if select_no < 0 or select_no >= len(group_bot_map.keys()):
            return False
        # Reset all selected of this group
        no = 0
        for key in group_bot_map:
            bot_cfg = group_bot_map[key]
            bot_cfg['selected'] = False
            if (no == select_no):
                bot_cfg['selected'] = True
            no += 1
        # Set
        print(f'Select Group: {owner_no}')
        print(f'Select Bot: {group_bot_map}')
        return True; 
    
    def get_now_bot(self, owner_no):
        ''' Get now selected bot '''
        owner_no = str(owner_no)
        group_bot_map = self.bot_map[owner_no]
        for key in group_bot_map:
            bot_cfg = group_bot_map[key]
            if bot_cfg.get('selected', True):
                return bot_cfg
        return None
   
    def set_pre_prompt(self, owner_no, pre_prompt):
        ''' Set pre prompt '''
        owner_no = str(owner_no)
        now_cfg = self.get_now_bot(owner_no)
        if (now_cfg):
            now_cfg['prefix_prompt'] = pre_prompt
            self.bot_map[owner_no][now_cfg['bot_name']] = now_cfg
            self.save_config()
            return True
        return False
   
    
# 应该使用缓存的方式来存储聊天记录, 防止异步操作导致的数据不一致{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
class ChatHistory():
    ''' 记录群成员聊天记录 '''
    def __init__(self, owner_no):
        date_str = time.strftime("%Y-%m-%d", time.localtime())
        session_path = os.path.join(
            os.path.dirname(__file__), f"chat_history/{owner_no}_{date_str}_session.json");
        log_path = os.path.join(
            os.path.dirname(__file__), f"chat_history/{owner_no}_{date_str}.log");
        ## 检查是否存在文件, 不存在则创建
        if not os.path.exists(session_path):
            with open(session_path, 'w') as file:
                json.dump([], file)
        if not os.path.exists(log_path):
            with open(log_path, 'w') as file:
                file.write("")
        self.session_path = session_path
        self.log_path = log_path
        self.target_no = owner_no
        
        # 读取session
        self.session = []
        self.session_len= 0
        self.log_cache = []
        with open(session_path, 'r') as file:
            self.session = json.load(file)
            for session_item in self.session:
                print(session_item)
                self.session_len += len(session_item['message'])
        
        # 初始化更新时间戳
        self.update_time = int(time.time())
    
    def add_message(self, group_id, user_id, message, extra = {}):
        ''' 添加消息 '''
        msg = {
            'group_id': group_id,
            'user_id': user_id,
            'message': message,
            'extra': extra
        }
        self.session.append(msg)
        self.log_cache.append(
            f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} {json.dumps(msg)}\n')
        self.update_time = int(time.time())
    
    def get_request_prompt(self, prefix_prompt):
        ''' 获取请求提示 '''
        request_prompt = ""
        if (len(prefix_prompt) > 0):
            request_prompt += prefix_prompt + '\n'
        request_prompt += '现在请根据以下聊天记录以及上述历史聊天记录进行聊天群的发言, 以下为新增聊天记录, 不同人之间的发言用 "|" 分隔: '
        no = 0
        for session_item in self.session:
            if (no == 0):
                request_prompt += f'{session_item["message"]}'
            else:
                request_prompt += f' | {session_item["message"]}'
            no += 1
        
        return request_prompt
        
    
    def save_session(self):
        ''' 保存session '''
        with open(self.session_path, 'w') as file:
            json.dump(self.session, file)
        # log尾部追加
        with open(self.log_path, 'a') as file:
            for log in self.log_cache:
                file.write(log)
        self.log_cache = []
    
    def on_clear(self):
        ''' 清空会话 '''
        print(f'{self.target_no}: 清空会话')
        self.session = []
        self.session_len = 0
        
        