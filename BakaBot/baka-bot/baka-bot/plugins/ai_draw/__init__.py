import random, nonebot
from nonebot import get_plugin_config, on_command
from nonebot.adapters import Message, Event, Bot
from nonebot.params import CommandArg, ArgPlainText, Arg
from nonebot.plugin import PluginMetadata
from nonebot_plugin_apscheduler import scheduler
import os, time
from .config import DrawBotConfig, UserConfig
from .comfy_client import FluxClient
import logging
import asyncio
from .db import UserDataDB

# 配置日志记录器
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

__plugin_meta__ = PluginMetadata(
    name="drawbot",
    description="",
    usage="",
)


botCfg = DrawBotConfig()
fluxClient = FluxClient(botCfg.server_address, botCfg.client_id)

@scheduler.scheduled_job("cron", second="*/5", id="job_save_session")
async def flux_client_monitor():
    # print("flux_client_monitor: ")
    # print(" status: ", fluxClient.status)
    # 初始化启动
    if fluxClient.status == "initing":
        asyncio.create_task(fluxClient.connect())
    # TODO 监控进程



def get_owner_no(event):
    if hasattr(event, 'group_id'):
        return event.group_id
    else:
        return event.user_id
    
###### 获取当前用户lora配置 ######
now_lora = on_command("now_lora", priority=5, block=True)
@now_lora.handle()
async def now_lora_handle(bot, event: Event):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    await now_lora.finish(userConfig.show_lora_info())

###### 查看当前支持的lora配置 ######
list_lora = on_command("list_lora", priority=5, block=True, aliases={"lora_list"})
@list_lora.handle()
async def list_lora_handle(bot, event: Event):
    await now_lora.finish(botCfg.show_support_lora())

###### 重置用户lora设置 ######
reset_lora = on_command("reset_lora", priority=5, block=True)
@reset_lora.handle()
async def reset_lora_handle(bot, event: Event):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    await reset_lora.finish(userConfig.reset_lora())

################## 设置用户lora配置 ########################
set_lora = on_command("set_lora", priority=5, block=True)
## 获取 lora 槽位
@set_lora.got("user_no", prompt="请输入lora槽位, 范围[0,3]")
async def got_user_no(user_no: Message = Arg()):
    try:
        user_no = int(user_no.extract_plain_text())
    except:
        await set_lora.reject("输入数据不是合法整数, 请重新输入lora槽位")
    if user_no < 0 or user_no > 3:
        await set_lora.reject("用户lora槽位范围[0,3]")
    return user_no

## 获取 lora 编号
@set_lora.got("lora_no", prompt=f"{botCfg.show_support_lora()}\n请输入安装lora的编号:")
async def got_lora_no(lora_no: Message = Arg()):
    try:
        lora_no = int(lora_no.extract_plain_text())
    except:
        await set_lora.reject("输入数据不是合法整数, 请重新输入lora编号")

    if lora_no < 0 or lora_no >= len(botCfg.lora_list):
        await set_lora.reject(f"选择lora编号错误, 输入范围[0, {len(botCfg.lora_list) - 1}], 请重新输入")

## 获取 lora 强度
@set_lora.got("lora_strength", prompt="请输入lora强度, 范围(0,1]浮点数, 为0代表关闭该槽位lora")
async def got_lora_strength(lora_strength: Message = Arg()):
    try:
        lora_strength = float(lora_strength.extract_plain_text())
    except:
        await set_lora.reject("输入值不是一个合法浮点数, 请重新输入lora强度")

    if lora_strength < 0 or lora_strength > 1:
        await set_lora.reject("lora强度范围(0,1], 请重新输入")

## 设置 lora 配置
@set_lora.handle()
async def set_lora_handle(event: Event, user_no: Message = Arg(), lora_no: Message = Arg(), lora_strength: Message = Arg()):
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
    try:
        guide = float(guide.extract_plain_text())
    except:
        await set_guide.reject("非法参数, 请重新输入浮点数")
    if guide < 0 or guide > 10:
        await set_guide.reject("引导参数范围(0,10), 请重新输入")
    
## 设置 k_sample 引导参数
@set_guide.handle()
async def set_guide_handle(event: Event, guide: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.save_guide(float(guide.extract_plain_text()))
    await set_guide.finish(res)

## 设置迭代步数
set_steps = on_command("set_step", priority=5, block=True, aliases={"set_steps"})
@set_steps.got("steps", prompt="请输入步长参数, 范围[5,50]整数:")
async def got_steps(steps: Message = Arg()):
    print(f'steps: {steps}')
    try:
        _steps = int(steps.extract_plain_text())
    except:
        await set_steps.reject("输入的步长不是整数, 请重新输入整数")
    if _steps < 5 or _steps > 50:
        await set_steps.reject("步长参数范围[5,50], 请重新输入")

## 设置 k_sample 迭代步数参数
@set_steps.handle()
async def set_steps_handle(event: Event, steps: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.save_step(int(steps.extract_plain_text()))
    await set_steps.finish(res)

## 获取 latent 分辨率
set_latent = on_command("set_wh", priority=5, block=True, aliases={"set_latent", "set_resolution"})
@set_latent.got("width", prompt="请输入宽度, 范围[128,1536]整数:")
async def got_width(width: Message = Arg()):
    try:
        width = int(width.extract_plain_text())
    except:
        await set_latent.reject("宽度参数不是整数, 请重新输入合法整数")
    if width < 128 or width > 1536:
        await set_latent.reject("宽度范围[128,1536], 请重新输入")

@set_latent.got("height", prompt="请输入高度, 范围[128,1536]整数:")
async def got_height(height: Message = Arg()):
    try:
        height = int(height.extract_plain_text())
    except:
        await set_latent.reject("高度参数不是整数, 请重新输入合法整数")
    if height < 128 or height > 1536:
        await set_latent.reject("高度范围[128,1536], 请重新输入")

## 设置 latent 分辨率
@set_latent.handle()
async def set_latent_handle(event: Event, width: Message = Arg(), height: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.save_resolution(int(width.extract_plain_text()), int(height.extract_plain_text()))
    await set_latent.finish(res)

## 设置种子
set_seed = on_command("set_seed", priority=5, block=True)
@set_seed.got("seed", prompt="请输入种子参数, 整数, 负数代表随机:")
async def got_seed(seed: Message = Arg()):
    # 检查是否为数字
    try:
        int(seed.extract_plain_text())
    except:
        await set_seed.reject("种子参数必须为整数, 请重新输入")

@set_seed.handle()
async def set_seed_handle(event: Event, seed: Message = Arg()):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    _success, res = userConfig.set_seed(int(seed.extract_plain_text()))
    await set_seed.finish(res)

## 获取用户所有设置
now_set = on_command("now_set", priority=5, block=True)
@now_set.handle()
async def now_set_handle(bot, event: Event):
    user_id = event.user_id
    userConfig = UserConfig(user_id)
    await now_set.finish(userConfig.show_setting())


################## 画图任务 ########################
draw_with_prompt = on_command("draw", priority=5, block=True)

@draw_with_prompt.handle()
async def draw_with_prompt_handle(bot, event: Event, prompt: Message = CommandArg()):
    # 一些简单校验
    prompt = prompt.extract_plain_text()
    if (len(prompt) <= 0):
        await draw_with_prompt.finish("请输入绘图引导")
    # 两个id获取
    user_id = event.user_id
    group_id = get_owner_no(event)
    # 先创建任务
    async with UserDataDB(botCfg.db_path) as db:
        await db.insert_user_task(user_id, group_id, "", prompt)
    # 检查 client 状态
    status, msg = check_client_status()
    if status != "running":
        await draw_with_prompt.finish(msg)

    print("draw_with_prompt_handle: ", prompt, user_id)
    await draw_with_prompt.finish("已设置绘图任务")


def check_client_status():
    if (fluxClient.status != "running"):
        if (fluxClient.status == "stop"):
            # TODO 检查什么进程导致的服务停止
            return [False, "任务已创建, 但有人在打电动, 游戏结束会自动拉起服务重新绘图"]
        elif (fluxClient.status == "initing"):
            return [False, "服务正在初始化, 但任务已创建, 初始化完成后会自动绘图"]
        elif (fluxClient.status == "starting"):
            return [False, "服务正在连接, 但任务已创建, 启动完成后会自动绘图"]
        else:
            return [False, "服务状态未知, 但任务已创建, 也许是出了bug, 修复后会自动绘图"]
    else:
        return [True, ""]