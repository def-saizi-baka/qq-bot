import random
from nonebot import get_plugin_config, on_command, on_message
from nonebot.adapters import Message, Event, Bot
from nonebot.params import CommandArg, ArgPlainText
from nonebot.plugin import PluginMetadata
from nonebot_plugin_apscheduler import scheduler
import os, time
from .config import Config, BotConfig, ChatHistory
from .poe_bot import PoeBot
import logging

# 配置日志记录器
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

import asyncio
__plugin_meta__ = PluginMetadata(
    name="chatbot",
    description="",
    usage="",
    config=Config,
)


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "bot_config.json")

plugin_cfg = get_plugin_config(Config)
tokens = {
    'p-b': plugin_cfg.P_B_KEY,
    'p-lat': plugin_cfg.P_LAT_KEY,
    'formkey': plugin_cfg.P_FORMER_KEY,
}
bot_cfg = BotConfig(CONFIG_PATH)
history_map = {}; # <group_id -> ChatHistory>

# 同步方式初始化机器人
print("Starting..." + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
poeInstance = PoeBot(10)
asyncio.run(poeInstance.init(tokens))
poeBot = poeInstance.client
print("Client created..." + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))


def get_owner_no(event):
    if hasattr(event, 'group_id'):
        return event.group_id
    else:
        return event.user_id
    
################################################
#### 机器人列表逻辑
################################################
now_bot_name = on_command("当前bot", priority=5, block=True)
@now_bot_name.handle()
async def handle_function(bot, event: Event):
    now_bot = bot_cfg.get_now_bot(get_owner_no(event))
    if (now_bot):
        await now_bot_name.finish(f"当前选择的模型: {now_bot['bot_name']}")
    else:
        await now_bot_name.finish(f"当前没有选择模型, 请使用指令 /选择bot 选择模型")

################################################
#### 机器人选择逻辑
################################################

select_bot = on_command("选择bot", priority=5, block=True)
@select_bot.handle()
async def handle_function(bot, event: Event, select_no: Message = CommandArg()):
    owner_no = get_owner_no(event)
    if select_no := select_no.extract_plain_text():
        select_no = int(select_no)
        await finish_select(select_bot, owner_no, select_no)
    else:
        now_bot = bot_cfg.get_now_bot(owner_no)
        if (now_bot != None):
            await select_bot.send(f'当前选择模型: {now_bot["bot_name"]}')
            

# 接收机器人选择参数
@select_bot.got("select_no", prompt=bot_cfg.get_select_msg())
async def get_select_no(bot, event: Event, select_no: str = ArgPlainText()):
    print(f"Got select_no: {select_no}")
    await finish_select(select_bot, get_owner_no(event), select_no)

# 完成选择
async def finish_select(handle, owner_no, select_no):
    select_no = int(select_no)
    if (bot_cfg.select_bot(owner_no, select_no)):
        bot_cfg.save_config()
        now_bot = bot_cfg.get_now_bot(owner_no)
        if (now_bot):
            await handle.finish(f"选择成功，当前选择的模型是: {now_bot['bot_name']}, 机器人会随机群内回复, 或使用 /chat 进行强制回复")
        else:
            await handle.finish(f"配置有误暂时无法选择该模型")
            
####################################################
#### 机器人对话逻辑
####################################################

import re

def extract_at_number(text):
    # 正则表达式匹配模式
    pattern = r'<le>\[at:qq=(\d+)\]</le>'
    
    # 使用 re.search 来搜索匹配项
    match = re.search(pattern, text)
    
    if match:
        qq_number = match.group(1)  # 获取匹配的第一组（即括号里的内容）
        return True, qq_number
    else:
        return False, ""
    
#### 会话定时保存
# 基于装饰器的方式
@scheduler.scheduled_job("cron", second="*/5", id="job_save_session")
async def onSaveSessionTimeout():
    del_list = []
    for owner_no in history_map:
        chatHistory: ChatHistory = history_map[owner_no]
        chatHistory.save_session()
        # 超时清空处理
        if (int(time.time()) - chatHistory.update_time > plugin_cfg.HISTORY_SESSION_INTERVAL):
            chatHistory.on_clear()
            del_list.append(owner_no)
            # del history_map[owner_no]
    for del_owner_no in del_list:
        del history_map[del_owner_no]
    
# 机器人发言逻辑
chat = on_message(priority=10, block=False)
@chat.handle()
async def handle_function(bot: Bot, event: Event):
    owner_no = str(get_owner_no(event))      # 群号 or 私聊发送者
    sender_id = str(event.get_user_id())     # 发送者
    print(f"Chat: {event} owner_no: {owner_no} sender_id: {sender_id} messgae: {event.get_message()}")
    # 白名单检测
    if (owner_no not in plugin_cfg.ALLOWED_GROUPS):
        return
    
    # 非字符串信息跳过
    message_str = event.get_plaintext()
    if (len(message_str) <= 0):
        return
    
    # 获取该群聊天记录管理实例
    if owner_no not in history_map:
        history_map[owner_no] = ChatHistory(owner_no)
    chatHistory: ChatHistory = history_map[owner_no]
    chatHistory.add_message(owner_no, sender_id, event.get_plaintext())
    
    # 触发概率
    rate = plugin_cfg.TRIGGER_CFG[owner_no]
    # 被 at 直接触发
    has_at, at_target = extract_at_number(event.get_event_description())
    if (has_at and at_target == str(bot.self_id)):
        rate = 1
    if (rate < 1 and rate < random.random()):
        return
    botCgf = bot_cfg.get_now_bot(owner_no)
    # 并发控制
    if (poeInstance.is_locked()):
        await chat.send("Chatbot is busy, please wait a moment")
        return
    # 生成回复语句
    success, res_msg = await get_chatbot_msg(chatHistory, botCgf)
    if (success):
        await chat.finish(res_msg)


# 机器人强制回复
force_chat = on_command("chat", priority=5, block=True)
@force_chat.handle()
async def handle_function(bot, event: Event):
    owner_no = str(get_owner_no(event))
    sender_id = str(event.get_user_id())     # 发送者
    botCgf = bot_cfg.get_now_bot(owner_no)
    if (botCgf == None):
        await force_chat.finish("请先选择机器人 /选择bot")
    if (poeInstance.is_locked()):
        await force_chat.finish("Chatbot is busy, please wait a moment")

    # 获取该群聊天记录管理实例
    if owner_no not in history_map:
        history_map[owner_no] = ChatHistory(owner_no)
    chatHistory: ChatHistory = history_map[owner_no]
    chatHistory.add_message(owner_no, sender_id, event.get_plaintext())
    
    success, res_msg = await get_chatbot_msg(chatHistory, botCgf)
    if (success):
        await force_chat.finish(res_msg)
    else:
        await force_chat.finish("bot已掉线, 请稍后再试")

# 获取机器人回复
async def get_chatbot_msg(chatHistory: ChatHistory, botCgf):
    try:
        poeInstance.on_lock()
        request_msg = chatHistory.get_request_prompt(botCgf['prefix_prompt'])
        async for chunk in poeBot.send_message(
            bot=botCgf['bot_name'], message=request_msg, chatId=botCgf['chatId']):
            pass   
        poeInstance.on_unlock()
        # 累计session清空
        chatHistory.on_clear()
        return True, chunk["text"]
    except Exception as e:
        logging.exception("捕获到异常")
        print(f"异常信息: {e}")
        poeInstance.on_unlock()

####################################################
# 机器人设定修改逻辑
####################################################
set_pre_prompt = on_command("bot设定修改", priority=5, block=True)
@set_pre_prompt.handle()
async def handle_function(bot, event: Event, pre_prompt: Message = CommandArg()):
    owner_no = get_owner_no(event)
    if pre_prompt := pre_prompt.extract_plain_text():
        if (bot_cfg.set_pre_prompt(owner_no, pre_prompt)):
            await set_pre_prompt.finish(f"修改完成")
        else:
            await set_pre_prompt.finish(f"修改失败")
    else:
        now_bot_cfg = bot_cfg.get_now_bot(owner_no)
        if (now_bot_cfg == None):
            await set_pre_prompt.finish("请先选择机器人 /选择bot")
        await set_pre_prompt.send(f'当前机器人 {now_bot_cfg['bot_name']} 设定: {now_bot_cfg["prefix_prompt"]}')
    pass

@set_pre_prompt.got("pre_prompt", prompt="请输入bot新设定")
async def get_pre_prompt(bot, event: Event, pre_prompt: str = ArgPlainText()):
    owner_no = get_owner_no(event)
    if (bot_cfg.set_pre_prompt(owner_no, pre_prompt)):
        now_bot = bot_cfg.get_now_bot(owner_no)
        await poeBot.chat_break(now_bot['bot_name'], chatId=now_bot['chatId'])
        await set_pre_prompt.finish(f"修改完成, 当前机器人设定: {pre_prompt}")
    else:
        await set_pre_prompt.finish(f"修改失败")


