import json
import os
import random
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import NudgeEvent
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.model import Group, Member
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex

# 插件信息
__name__ = "戳一戳"
__description__ = "自定义戳一戳随机回复"
__author__ = "saizi"
__usage__ = "戳机器人"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}

# 打开配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

__openCmd__ = "#open chuoyichuo"
__closeCmd__ = "#close chuoyichuo"
re_pattern = f"({__openCmd__})|({__closeCmd__})"

@channel.use(ListenerSchema(listening_events=[NudgeEvent]))
async def chuoyichuo(app: Ariadne, event: NudgeEvent):
    if event.target == app.account:
        if event.group_id not in config_info['on']:
            return
        choice = random.randint(0, len(config_info['ans'])-1)
        await app.send_group_message(
            event.group_id, MessageChain(config_info['ans'][choice]))


# 模块开关
@listen(GroupMessage)
@decorate(MatchRegex(regex=re_pattern))
async def chuoyichuoSwitch(app: Ariadne, message: MessageChain, group: Group):
    cmd = str(message)
    group_id = group.id
    # 开启指令
    if(cmd == __openCmd__):
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

            


