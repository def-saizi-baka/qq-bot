from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Plain, Quote
from graia.ariadne.model import Group, Member, MemberInfo
from graia.ariadne.message.element import At, Plain, Image
from graia.ariadne.event.message import GroupMessage, Group
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex

import os, json

__name__ = "SetSpecialName"
__description__ = "设置用户特殊荣誉"
__author__ = "SaiZi"
__usage__ = "#setspn @要设置的人 特殊名称(<=6个字符) #setnkn @要设置的人 名称(<=20个字符)"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

# 配置文件初始化
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

# 匹配选项
set_sp_cmd = "#setspn"
set_nk_cmd = "#setnkn"
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_cmd_pattern = f"(^{set_sp_cmd})|(^{set_nk_cmd})" # (^#setspn)|(^#setnkn)
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full= False))
async def setSpecialName(app: Ariadne, message: MessageChain, group: Group):
    # 开关限制
    if(group.id not in config_info["on"]):
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
        return
    # 获取除去@的部分
    message_plain = str(MessageChain(message.get(Plain))).replace(' ', '')
    print(f'[info]: 检测到{re_cmd_pattern}, plain: {message_plain}')

    # 查找关键词
    if(message_plain.find(set_sp_cmd) == 0 or message_plain.find(set_nk_cmd)==0):
        # 获取at的成员
        if(message.has(At)):
            # 获取待修改用户的成员对象信息
            modified_member_id = message.get(At)[0].target
            modifiedMembers = await app.get_member(group, modified_member_id)
            memberInfo = await modifiedMembers.get_info()
            # 改群特殊头衔
            if(message_plain[:len(set_sp_cmd)] == set_sp_cmd):
                memberInfo.special_title = message_plain[len(set_sp_cmd):]
            # 改群名片 
            else:
                memberInfo.name = message_plain[len(set_nk_cmd):]
            
            # 判断长度合法, 进行修改
            if(0<len(memberInfo.special_title)<= 6 or 0<len(memberInfo.name)<=20):
                await app.modify_member_info(modifiedMembers, memberInfo)
                await app.send_group_message(group, MessageChain("(ᗜˬᗜ)"))
            else:
                await app.send_group_message(group, MessageChain("设置的长度非法"))

            

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