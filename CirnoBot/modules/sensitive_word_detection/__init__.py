import json
import os
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain, Source
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from aiohttp.client_exceptions import ClientResponseError

# 插件信息
__name__ = "敏感词检测"
__description__ = "敏感词检测"
__author__ = "saizi"
__usage__ = "检测到敏感词并撤回"

channel = Channel.current()

# # 指令部分
# __OPEN__ = f"#open {__name__}"
# __CLOSE__ = f"#close {__name__}"
# re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

# 打开配置文件
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)


question_key = "添加敏感词"
delete_key = "删除敏感词"
list_key = "ls sensitive_words"
channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def check_alive(app: Ariadne, message: MessageChain, sender: Member,
                      group: Group, source: Source):
    ss = str(message).strip()
    # 关键字起始点
    question_src = ss.find(question_key)
    delete_src = ss.find(delete_key)
    list_src = ss.find(list_key)
    # 检测到添加指令
    if question_src != -1 or delete_src != -1:
        add_ans = ss[question_src + len(question_key):]
        add_ans = add_ans.strip()
        delete_ans = ss[delete_src + len(delete_key):].strip()
        delete_ans = delete_ans.strip()
        # 检测权限
        if sender.id in config_info['root']:
            # 检测指令类型 如果是添加
            if question_src != -1:
                if add_ans not in config_info["keyword"]:
                    config_info["keyword"].append(add_ans)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(config_info))
                    await app.send_group_message(group, MessageChain("添加成功"))
                else:
                    await app.send_group_message(group, MessageChain("该敏感词已经存在"))

            else:   # 删除
                if delete_ans in config_info["keyword"]:
                    config_info["keyword"].remove(delete_ans)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(config_info))
                    await app.send_group_message(group, MessageChain("删除成功"))
                else:
                    await app.send_group_message(group, MessageChain("未找到该敏感词"))

        else:
            await app.send_group_message(group, MessageChain("⑨: 权限不足, 无法修改敏感词列表"))

        return
    # 列出敏感词
    if list_src != -1:
        print(str(config_info['keyword']))
        return
    # 检测敏感词
    for sensitive_word in config_info['keyword']:
        if sensitive_word in str(message):
            msg_list = [
                At(sender.id),
            ]
            # 撤回消息
            try:
                await app.recall_message(source, group)
                # 发送警告
                msg_list.append('检测到敏感词，已撤回')
                await app.send_group_message(
                    group, MessageChain(msg_list))
                break
            except (ClientResponseError, PermissionError):
                msg_list.append('检测到敏感词, Bot当前权限不足, 无法撤回')
                # 发送警告
                await app.send_group_message(
                    group, MessageChain(msg_list))
                break

