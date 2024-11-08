import json, os, time
from typing import Union

# 机器人基础配置
class DrawBotConfig():
    def __init__(self) -> None:
        self.lora_list = [
            {"name": "anime", "path": "anime_aesthetic_lora.safetensors", "desc": "Anime Aesthetic"},
            # {"name": "Lora1", "path": ""},
            # {"name": "Lora2", "path": ""},
            # {"name": "Lora3", "path": ""},
        ]

default_config = {
    "lora": [
        {"name": "Lora0", "strength": 0, "path": ""},
        {"name": "Lora1", "strength": 0, "path": ""},
        {"name": "Lora2", "strength": 0, "path": ""},
        {"name": "Lora3", "strength": 0, "path": ""},
    ],
    "k_sample": {
        "guide": 3.5,
        "step": 20,
        "resolution": [
            1024,
            1024
        ]
    },
    "noise": {
        "seed": -1
    }
}

# 用户配置目录
class UserConfig():
    def __init__(self, user_id: int) -> None:
        """初始化用户配置

        Args:
            user_id (int): 用户ID(QQ号)
        """
        config_path = os.path.join(
            os.path.dirname(__file__), f"user_config/{user_id}.json")
        # 检查是否存在文件, 不存在则用 default_config 创建
        if not os.path.exists(config_path):
            with open(config_path, 'w') as file:
                json.dump(default_config, file)

        # 读取配置
        with open(config_path, 'r') as file:
            self.config = json.load(file)
        
        self.config_path = config_path
    
    def _save_config(self) -> None:
        ''' 保存配置 '''
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file)

    ##### lora 配置 #####
    
    def set_lora(self, user_no: int, lora_no: int, lora_strength: float, lora_cfg: list[dict]) -> Union[bool, str]:
        """
        设置 lora 配置
        Args:
            user_no: 用户lora槽位
            lora_no: lora 编号
            lora_strength: lora 强度
        """
        user_lora = self.config['lora']
        # 检查用户lora槽位是否存在
        if (user_no >= len(user_lora) or user_no < 0):
            return False, "用户Lora槽位不存在"
        # 检查lora编号是否存在
        if (lora_no >= len(lora_cfg) or lora_no < 0):
            return False, "指定的Lora编号不存在"
        # 检查lora强度是否合法
        if (lora_strength < 0 or lora_strength > 1):
            return False, "Lora强度不合法"
        
        # 保存配置
        target_lora = lora_cfg[lora_no]
        edit_lora = user_lora[user_no]
        edit_lora['name'] = target_lora['name']
        edit_lora['strength'] = lora_strength
        edit_lora['path'] = target_lora['path']

        user_lora[user_no] = edit_lora
        self.config['lora'] = user_lora
        self._save_config()

        return True, f"已保存用户Lora配置: {edit_lora['name']}, 强度: {lora_strength}, 槽位: {user_no}"
    
    def reset_lora(self) -> Union[bool, str]:
        """重置用户 lora 配置
        """
        self.config['lora'] = default_config['lora']
        self._save_config()
        return [True, "已重置用户Lora配置"]

    def show_lora_info(self) -> str :
        """获取发送给用户显示的 lora 字符串 /now_lora
        """
        lora_str = ""
        for i in range(len(self.config['lora'])):
            lora_info = self.config['lora'][i]
            if (lora_info['lora_strength'] > 0):
                lora_str += f"{i}. name: {lora_info['name']}, strength: {lora_info['lora_strength']}\n"
            else:
                lora_str += f"{i}. name: {lora_info['name']}, strength: 未使用\n"
        return lora_str
    

    ##### k_sample 配置 #####

    def save_guide(self, value):
        """设置引导参数

        Args:
            value (float): 设置value
        """
        if (value <= 0 or value > 10):
            return False, "引导参数不合法"
        self.config['k_sample']['guide'] = value
        self._save_config()
    
    def save_step(self, value):
        """设置步长参数

        Args:
            value (int): 设置value
        """
        if (value < 5 or value > 50):
            return False, "步长参数不合法"
        self.config['k_sample']['step'] = int(value)
        self._save_config()
    
    def save_resolution(self, width, height):
        """设置分辨率参数

        Args:
            width (int): 宽度
            height (int): 高度
        """
        if (width < 128 or height < 128 or width > 1536 or height > 1536):
            return False, "分辨率参数不合法"
        self.config['k_sample']['resolution'] = [int(width), int(height)]
        self._save_config()

    #### noise 配置 ####
    def set_seed(self, seed):
        """设置种子参数

        Args:
            seed (int): 设置value
        """
        self.config['noise']['seed'] = int(seed)
        self._save_config()

    #### Prompt ####


    # def set_config(self, key, value):
    #     ''' 设置配置 '''
    #     self.config[key] = value
    #     self._save_config()