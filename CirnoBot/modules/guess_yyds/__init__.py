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
import random, os, json
import requests 
# 插件信息
__name__ = "能不能好好说话"
__description__ = "猜词"
__author__ = "SaiZi"
__usage__ = "在群内发送 #guess/GUESS(请不要随便大写) 内容(缩写) 即可"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


# 指令部分
guess_cmd = "#guess"
GUESS_cmd = "#GUESS"
re_cmd_pattern = f"(^{guess_cmd})|(^{GUESS_cmd})"
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

# 打开配置文件
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)


@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def guess_yyds(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if(group.id not in config_info["on"]):
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
        return
    try:
        message_text = MessageChain(message.get(Plain))
        message_text = str(message_text).replace(' ', '')
        # 删除图片与at信息, 只保留文本
        if guess_cmd in str(message):
            # 触发指令
            if message_text.find(guess_cmd) == 0 and len(message_text) > len(guess_cmd)+1:
                guess_res = await get_guess(message_text[len(guess_cmd):])
                respond_str = [At(member.id), guess_res]
                await app.send_group_message(group, MessageChain(respond_str))

        if GUESS_cmd in str(message):
            # 触发指令
            if message_text.find(GUESS_cmd) == 0 and len(message_text) > len(GUESS_cmd)+1:
                guess_res = get_guess_ss(message_text[len(GUESS_cmd):])
                respond_str = [At(member.id), guess_res]
                await app.send_group_message(group, MessageChain(respond_str))

    except:
        import traceback, sys
        traceback.print_exc()  # 打印异常信息
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
        await app.send_group_message(config_info["log_group"], MessageChain(error))

   
async def get_guess(guess_str)->str:
    url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    headers = {
        "referer": "https://lab.magiconch.com/nbnhhsh/"
    }
    data = {
        "text": guess_str
    }
    resp=requests.post(url,headers=headers,data=data)
    res = (resp.json())[0]
    res = (resp.json())[0]
    if "trans" in res.keys():
        print(f"res['trans']={res['trans']}")
        if res['trans']==None or len(res['trans']) == 0:
            return "未查到相关信息, 换个词试试吧"
        res_str='查询结果为'
        for rr in res['trans']:
            res_str+='\n'
            res_str+=rr
        return res_str
    else:
        if len(res['inputting']) == 0:
            return "未查到相关信息, 换个词试试吧"
        res_str='查询结果为'
        for rr in res['inputting']:
            res_str+='\n'
            res_str+=rr
        return res_str

    


def get_guess_ss(guess_str)->str:
    from .bnhhsh_slave.bnhhsh import dp
    res = dp(guess_str)
    if len(res) == 0:
        return "未查到相关信息, 换个词试试吧"
    res_str='查询结果为:\n'
    res_str += res
    return res_str


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