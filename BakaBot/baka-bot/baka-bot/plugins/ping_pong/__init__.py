from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot import V11Bot as Bot, V11Event as Event
# from nonebot.adapters.onebot.v11 import message as Message
from nonebot.adapters.onebot.v11 import MessageSegment
# from arclet.alconna import Alconna, Args
# from nonebot_plugin_alconna import Match, on_alconna, At

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="ping_pong",
    description="",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)

from nonebot import on_command, on_request #, on_message
# from nonebot.rule import 

ping_pong = on_command('ping', priority=5, block=True)
@ping_pong.handle()
async def handle():
    await ping_pong.finish("pong")

# 加群自动同意
group_request = on_request(priority=5, block=True)
@group_request.handle()
async def handle(bot: Bot, event: Event.GroupRequestEvent):
    await bot.set_group_add_request(flag=event.flag, sub_type=event.sub_type, approve=True)
    await bot.send(event, [MessageSegment.at(event.user_id), ' 欢迎入群, \n群主为机器人, \n相关指令操作请查看群公告, \n软件 / 某些网络问题请 ', MessageSegment.at(3281272972)])

# test_handle = on_message(priority=50, block=True)
# @test_handle.handle()
# async def handle(bot: Bot, event: Event):
#     print(event.get_event_description())
#     print(bot.self_id)
    # msg = event.get_message() 
    # for segment in msg:
        # print(segment)
    
    