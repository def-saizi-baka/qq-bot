import json
import os
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain
from graia.ariadne.event.mirai import MemberJoinEvent, MemberJoinRequestEvent
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex
# 插件信息
__name__ = "入群欢迎"
__description__ = "同意新成员入群并欢迎"
__author__ = "saizi"
__usage__ = "加群"

channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

# 配置文件初始化
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

@listen(MemberJoinEvent)
async def welcome(app: Ariadne, group: Group, member: Member):
    # 检查是否开启服务
    if(group.id not in config_info["on"]):
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
        return

    if str(group.id) in config_info.keys():
        respond_msg = [
            At(member.id),
            Plain(' '),
            Plain(config_info[str(group.id)])
        ]

        await app.send_group_message(
            group, MessageChain(respond_msg))
    else:
        await app.send_group_message(
            group, MessageChain("该群未设置欢迎回复语, 请前往后端设置"))


# MemberJoinRequestEvent
@listen(MemberJoinRequestEvent)
async def procesing_joinRequest(app: Ariadne, event: MemberJoinRequestEvent):
    if str(event.source_group) in config_info.keys():
        print("收到用户加群请求")
        group_member_num = len(await app.get_member_list(event.source_group))+1
        print(f"当前群人数为{group_member_num}")
        if group_member_num < 500:
            print(f"已同意 {event.supplicant} 进群")
            await event.accept()
        else:
            return
