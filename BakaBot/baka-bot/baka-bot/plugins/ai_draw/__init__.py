import random
from nonebot import get_plugin_config, on_command, on_message
from nonebot.adapters import Message, Event, Bot
from nonebot.params import CommandArg, ArgPlainText, Arg
from nonebot.plugin import PluginMetadata
from nonebot_plugin_apscheduler import scheduler
import os, time
from .config import DrawBotConfig, UserConfig
import logging

# 配置日志记录器
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

import asyncio
__plugin_meta__ = PluginMetadata(
    name="drawbot",
    description="",
    usage="",
)


botCfg = DrawBotConfig()

def get_owner_no(event):
    if hasattr(event, 'group_id'):
        return event.group_id
    else:
        return event.user_id
    
###### 获取当前用户lora配置 ######
now_lora = on_command("now_lora", priority=5, block=True)
@now_lora.handle()
async def handle_function(bot, event: Event):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    await now_lora.finish(userConfig.show_lora_info())

###### 查看当前支持的lora配置 ######
list_lora = on_command("list_lora", priority=5, block=True)
@list_lora.handle()
async def handle_function(bot, event: Event):
    await now_lora.finish(botCfg.show_support_lora())

###### 重置用户lora设置 ######
reset_lora = on_command("reset_lora", priority=5, block=True)
@reset_lora.handle()
async def handle_function(bot, event: Event):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    await reset_lora.finish(userConfig.reset_lora())

################## 设置用户lora配置 ########################
set_lora = on_command("set_lora", priority=5, block=True)
## 获取 lora 槽位
@set_lora.got("user_no", prompt="请输入lora槽位, 范围[0,3]")
async def got_user_no(user_no: Message = Arg()):
    user_no = int(user_no.extract_plain_text())
    if user_no < 0 or user_no > 3:
        await set_lora.reject("用户lora槽位范围[0,3]")
    return user_no

## 获取 lora 编号
@set_lora.got("lora_no", prompt=f"{botCfg.show_support_lora()}\n请输入安装lora的编号:")
async def got_lora_no(lora_no: Message = Arg()):
    lora_no = int(lora_no.extract_plain_text())
    if lora_no < 0 or lora_no >= len(botCfg.lora_list):
        await set_lora.reject(f"选择lora编号错误 + [0, {len(botCfg.lora_list) - 1}]")

## 获取 lora 强度
@set_lora.got("lora_strength", prompt="请输入lora强度, 范围(0,1]浮点数, 为0代表关闭该槽位lora")
async def got_lora_strength(lora_strength: Message = Arg()):
    lora_strength = float(lora_strength.extract_plain_text())
    if lora_strength < 0 or lora_strength > 1:
        await set_lora.reject("lora强度范围(0,1]")

## 设置 lora 配置
@set_lora.handle()
async def got_func(event: Event, user_no: Message = Arg(), lora_no: Message = Arg(), lora_strength: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _, res = userConfig.set_lora(
        int(user_no.extract_plain_text()), 
        int(lora_no.extract_plain_text()), 
        float(lora_strength.extract_plain_text()), 
        botCfg.lora_list)
    
    await set_lora.finish(res)

################## 设置用户k_sample配置 ########################

## 获取 k_sample 引导参数
set_guide = on_command("set_guide", priority=5, block=True)
@set_guide.got("guide", prompt="请输入引导参数, 范围(0,10)浮点数:")
async def got_guide(guide: Message = Arg()):
    guide = float(guide.extract_plain_text())
    if guide < 0 or guide > 10:
        await set_guide.reject("引导参数范围(0,10)")
    
## 设置 k_sample 引导参数
@set_guide.handle()
async def got_func(event: Event, guide: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.save_guide(float(guide.extract_plain_text()))
    await set_guide.finish(res)

## 设置迭代步数
set_steps = on_command("set_step", priority=5, block=True, aliases={"set_steps"})
@set_steps.got("steps", prompt="请输入步长参数, 范围[5,50]整数:")
async def got_steps(steps: Message = Arg()):
    steps = int(steps.extract_plain_text())
    if steps < 5 or steps > 50:
        await set_steps.reject("步长参数范围[5,50]")

## 设置 k_sample 引导参数
@set_steps.handle()
async def got_func(event: Event, steps: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.save_step(int(steps.extract_plain_text()))
    await set_steps.finish(res)

## 获取 latent 分辨率
set_latent = on_command("set_wh", priority=5, block=True, aliases={"set_latent", "set_resolution"})
@set_latent.got("width", prompt="请输入宽度, 范围[128,1536]整数:")
async def got_width(width: Message = Arg()):
    width = int(width.extract_plain_text())
    if width < 128 or width > 1536:
        await set_latent.reject("宽度范围[128,1536]")

@set_latent.got("height", prompt="请输入高度, 范围[128,1536]整数:")
async def got_height(height: Message = Arg()):
    height = int(height.extract_plain_text())
    if height < 128 or height > 1536:
        await set_latent.reject("高度范围[128,1536]")

## 设置 latent 分辨率
@set_latent.handle()
async def got_func(event: Event, width: Message = Arg(), height: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.save_resolution(int(width.extract_plain_text()), int(height.extract_plain_text()))
    await set_latent.finish(res)


