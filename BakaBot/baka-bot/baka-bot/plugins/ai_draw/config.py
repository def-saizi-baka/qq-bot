import json, os, time
import random
import copy
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
        self.client_id = "c1b1b1b1-1b1b-1b1b-1b1b-1b1b1b1b1b1b"
        self.server_address = "127.0.0.1:8188"
        
        # 加载基础prompt配置文件
        self.t2i_base_prompt = json.load(
            open(os.path.join(os.path.dirname(__file__), "Api_Text2Img.json"), 'r', encoding='utf-8')
        )
        self.i2i_base_prompt = json.load(
            open(os.path.join(os.path.dirname(__file__), "Api_Img2Img.json"), 'r', encoding='utf-8')
        )
    
    def show_support_lora(self) -> str:
        """获取支持的 lora 列表

        Returns:
            str: 发送给用户的 lora 列表展示字符串
        """
        lora_str = "当前支持的 Lora 列表:\n"
        for i in range(len(self.lora_list)):
            lora_info = self.lora_list[i]
            lora_str += f"{i}. name: {lora_info['name']}, desc: {lora_info['desc']}\n"
        
        return lora_str

DEFAULT_CONFIG = {
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
                json.dump(DEFAULT_CONFIG, file)

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

        return [True, f"已保存用户Lora配置: {edit_lora['name']}, 强度: {lora_strength}, 槽位: {user_no}"]
    
    def reset_lora(self) -> Union[bool, str]:
        """重置用户 lora 配置
        """
        self.config['lora'] = DEFAULT_CONFIG['lora']
        self._save_config()
        return "已重置用户Lora配置"

    def show_lora_info(self) -> str :
        """获取发送给用户显示的 lora 字符串 /now_lora
        """
        lora_str = "当前用户 Lora 配置:\n"
        for i in range(len(self.config['lora'])):
            lora_info = self.config['lora'][i]
            if (lora_info['strength'] > 0):
                lora_str += f"{i}. name: {lora_info['name']}, strength: {lora_info['strength']}\n"
            else:
                lora_str += f"{i}. name: {lora_info['name']}, strength: 未使用\n"
        return lora_str
    

    ##### k_sample 配置 #####

    def save_guide(self, value):
        """设置引导参数

        Args:
            value (float): 设置value
        """
        if (value <= 0 or value >= 10):
            return False, "引导参数不合法, 范围 (0, 10) "
        self.config['k_sample']['guide'] = value
        self._save_config()
        return [True, f"已保存引导参数为: {value}"]
    
    def save_step(self, value):
        """设置步长参数

        Args:
            value (int): 设置value
        """
        if (value < 5 or value > 50):
            return False, "步长参数不合法, 范围 [10, 50]"
        self.config['k_sample']['step'] = int(value)
        self._save_config()
        return [True, f"已保存步长参数为: {value}"]
    
    def save_resolution(self, width, height):
        """设置分辨率参数

        Args:
            width (int): 宽度
            height (int): 高度
        """
        if (width < 128 or height < 128 or width > 1536 or height > 1536):
            return False, "分辨率参数不合法, 范围 [128, 1536]"
        self.config['k_sample']['resolution'] = [int(width), int(height)]
        self._save_config()
        return [True, f"已保存分辨率参数为: {width}x{height}"]

    #### noise 配置 ####
    def set_seed(self, seed):
        """设置种子参数

        Args:
            seed (int): 设置value
        """
        self.config['noise']['seed'] = int(seed)
        self._save_config()
        return [True, f"已保存种子参数为: {seed}"]

    def get_seed(self):
        """获取用户种子

        Returns:
            int: 种子参数
        """
        seed = self.config['noise']['seed']
        if (seed < 0): # 随机种子
            seed = random.getrandbits(64)

        return int(seed)

    def show_setting(self):
        show_str = "当前用户配置:\n"
        show_str += f"引导参数: {self.config['k_sample']['guide']}\n"
        show_str += f"步长参数: {self.config['k_sample']['step']}\n"
        show_str += f"分辨率参数: \n"
        show_str += f"  宽度: {self.config['k_sample']['resolution'][0]}\n"
        show_str += f"  高度: {self.config['k_sample']['resolution'][1]}\n"
        show_str += f"种子参数: {self.config['noise']['seed']}\n"
        return show_str

    #### Prompt ####
    
    def generate_t2i_prompt(self, t2i_config) -> dict:
        """根据用户之前的生成用户 Prompt text2img

        Returns:
            str: 用户 Prompt
        """
        user_prompt = copy.deepcopy(t2i_config['prompt'])

        # lora加载器设置
        loraLoaderInputs = user_prompt['66']['inputs']
        apply_no = 1
        for i in range(len(self.config['lora'])):
            lora_info = self.config['lora'][i]
            if (lora_info['strength'] > 0):
                lora_key = f"lora_{apply_no}"
                loraLoaderInputs[lora_key] = {
                    "on": True,
                    "lora": lora_info['path'],
                    "strength": lora_info['strength']
                }
                apply_no += 1

        user_prompt['66']['inputs'] = loraLoaderInputs
        
        # k_sample设置
        ## step
        user_prompt['17']['inputs']['steps'] = self.config['k_sample']['step']
        ## guidance
        user_prompt['36']['inputs']['guidance'] = self.config['k_sample']['guide']
        ## resolution(latent)
        user_prompt['78']['inputs']['width'] = self.config['k_sample']['resolution'][0]
        user_prompt['78']['inputs']['height'] = self.config['k_sample']['resolution'][1]
        ## noise seed
        user_prompt['25']['inputs']['noise_seed'] = self.get_seed()

        return user_prompt
    
    def generate_i2i_prompt(self, i2i_config) -> str:
        """根据用户之前的生成用户 Prompt img2img

        Returns:
            str: 用户 Prompt
        """
        # TODO


    # def set_config(self, key, value):
    #     ''' 设置配置 '''
    #     self.config[key] = value
    #     self._save_config()