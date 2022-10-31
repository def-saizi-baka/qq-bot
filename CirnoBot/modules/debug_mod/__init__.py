import json
import os
import random
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.model import Group, Member, Friend
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Voice, Image
from graia.ariadne.util.saya import decorate, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex
from graiax import silkcoder
# 插件信息
__name__ = "Debug"
__description__ = "Debug"
__author__ = "saizi"
__usage__ = "Debug"

channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

base_path = os.path.dirname(__file__)


re_cmd_pattern = "#debug"

@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def chuoyichuo(app: Ariadne, group: Group, message: MessageChain):
    
    await app.send_group_message(group, MessageChain(Image(path=base_path+"/temp.gif")))
# async def recall_detector(app: GraiaMiraiApplication, group: Group, member: Member):
