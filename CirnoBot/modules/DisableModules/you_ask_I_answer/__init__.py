import json
import os
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# 插件信息
__name__ = "niwenwoda"
__description__ = "你问我答"
__author__ = "SaiZi"
__usage__ = "在群内发送配置文件中给定的口令"
# 当前文件路径
current_path = os.path.dirname(__file__)

channel = Channel.current()
channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

# 设问关键字
question_key = "我说"
answer_key = "你答"
delete_key = "不要回答"

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def you_ask(app: Ariadne, message: MessageChain,
                           group: Group, member: Member):
    ss = message.asDisplay().strip()
    # 关键字起始点
    question_src = ss.find(question_key)
    ans_src = ss.find(answer_key)
    delete_src = ss.find(delete_key)
    # 获取当前json文件配置
    with open(current_path + '/config.json', 'r', encoding='utf-8') as f:
        config_info = json.load(f)
    # 如果检测到问题关键词
    if ss in config_info.keys():
        await app.sendGroupMessage(group, MessageChain.create(config_info[ss]['ans']))
    # 如果检测到删除关键词
    if delete_src != -1:
        delete_question = ss[delete_src+len(delete_key):]
        delete_question = delete_question.strip()
        msg_str = ''
        # 若检测到待删除问题
        if delete_question in config_info.keys():
            # 判断是否有删除权限
            if member.id in config_info[delete_question]['op_id']:
                msg_str = '删除成功'
                config_info.pop(delete_question)
                with open(current_path + '/config.json', 'w', encoding='utf-8') as f:
                    f.write(json.dumps(config_info))
            else:
                msg_str = '没有删除权限'
        else:
            msg_str = '未找到该问题'
        await app.sendGroupMessage(group, MessageChain.create(msg_str))

    # 如果有你说我答关键字
    if question_src != -1 and ans_src != -1:
        # 获取问答,提问者的id
        questioner = member.id
        question = ss[question_src + len(question_key):ans_src]
        ans = ss[ans_src + len(answer_key):]
        # 将问答前后多余部分删除
        question = question.strip()
        ans = ans.strip()
        # 添加新的条目
        tmp = {"op_id": [questioner, 744870006], "ans": ans}
        config_info[question] = tmp
        # 写入json文件
        with open(current_path + '/config.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(config_info))
        await app.sendGroupMessage(group, MessageChain.create('添加成功, 快来问我试试吧'))