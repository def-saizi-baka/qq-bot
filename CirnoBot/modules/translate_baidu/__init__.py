import hashlib
import requests
import aiohttp
import os
import json
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Plain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain, Image
from graia.ariadne.event.message import GroupMessage, Group
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex
import random

# 插件信息
__name__ = "自动翻译"
__description__ = ""
__author__ = "saizi"
__usage__ = ""

channel = Channel.current()

# 配置文件初始化
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

# 匹配选项
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"


cmd_list = ["www.", "http", "transfer help", "氪金 help", "本群月内总结", "guess", "GUESS", "#", "/", "cmd help", "cmdhelp"]

url = config_info["url"]
appid = config_info["appid"]
salt = config_info["salt"]
passkey = config_info["passkey"]

# 字符表
import string
china_punc = '\u3002\uff1f\uff01\uff0c\u3001\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u300a\u300b\u3008\u3009\u3010\u3011\u300e\u300f\u300c\u300d\ufe43\ufe44\u3014\u3015\u2026\u2014\uff5e\ufe4f\uffe5'
punc=string.punctuation+china_punc

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def instant_translation(app: Ariadne, message: MessageChain, group: Group, member: Member):
    message_str_list = message.get(Plain)
    message_text = MessageChain(message_str_list)
    message_text = str(message_text).strip()
    # 不对过于长的文本进行翻译
    if len(message_text)>=100 :
        print("文本过长,取消翻译")
        return
    # 没有开启这一项功能
    if(group.id not in config_info["on"] or len(message_text) == 0):
        return
        
    # 不对指令进行翻译
    for cmd in cmd_list:
        if message_text.find(cmd)==0:
            return

    # print("检测为中文, 不进行翻译")
    if isChinese(message_text):
        return

    try: 
        respond_str = await get_translate(message_text)
        if len(respond_str) > 0:
            if "⑨" in respond_str:
                await app.send_group_message(config_info["log_group"], MessageChain(respond_str))
            else:
                await app.send_group_message(group, MessageChain(respond_str))
    except:
        import traceback, sys
        traceback.print_exc()  # 打印异常信息
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        respond_str = error
        await app.send_group_message(config_info["log_group"], MessageChain(respond_str))

# 模块开关
@listen(GroupMessage)
@decorate(MatchRegex(regex=re_switch_pattern))
async def chuoyichuoSwitch(app: Ariadne, message: MessageChain, group: Group):
    cmd = str(message)
    group_id = group.id
    # 开启指令
    if(cmd == __OPEN__):
        if(group_id in config_info['on']):
            await app.send_group_message(
                group_id, MessageChain(f"{__name__}已经开启啦")
            )
        else:
            config_info['on'].append(group_id)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(config_info))

            await app.send_group_message(
                group_id, MessageChain(f"{__name__}开启成功")
            )    
    # 关闭指令
    else:
        if(group_id not in config_info['on']):
            await app.send_group_message(
                group_id, MessageChain(f"{__name__}已经关闭啦")
            )
        else:
            config_info['on'].remove(group_id)
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(config_info))

            await app.send_group_message(
                group_id, MessageChain(f"{__name__}关闭成功")
            )


async def get_translate(query_str: str):
    sign = (appid+query_str+salt+passkey).encode("UTF-8")
    md5_code = hashlib.md5(sign).hexdigest()
    data = {
        "q":query_str,
        "from": "auto",
        "to": "zh",
        "appid": appid,
        "salt": salt,
        "sign": md5_code
        }
    res = requests.post(url, data=data)
    res = res.json()
    # 出错
    if "error_code" in res.keys():
        if res["error_code"]=="54001":
            return "⑨: 字符编码错误!"
        elif res["error_code"]=="54003":
            return "⑨: 调用翻译速度太快啦!"
        elif res["error_code"]=="52001":
            return "⑨: 超时，不知道说的是啥!"
        else:
            return f"⑨: 其他错误，错误代码为{res['error_code']}, 错误信息为{res['error_msg']}"
    else:
        print(f'当前语言: {res["from"]}')
        if res["from"] == "zh":
            return ""
        else:
            return str(res["trans_result"][0]["dst"]+'#'+res["from"])


def isChinese(word):
    chinese_cnt=0
    not_cnt=0
    punc_num=0
    # 计数查找
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            chinese_cnt+=1
        elif ch in punc:
            punc_num+=1
        else:
            not_cnt+=1
    # print(chinese_cnt, not_cnt, punc_num)
    # 颜文字判断
    if not_cnt == 0 and chinese_cnt==0:
        return True
    # 中英文判断
    if not_cnt == 0 or chinese_cnt>=not_cnt:
        return True
    
    return False