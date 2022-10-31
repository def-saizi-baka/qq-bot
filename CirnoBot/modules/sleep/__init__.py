from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Plain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain, Image
from graia.ariadne.event.message import GroupMessage, Group
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex
import random, os, json
# 插件信息
__name__ = "GoToSleep"
__description__ = "获得6小时精致睡眠"
__author__ = "SaiZi"
__usage__ = "在群内发送 #Sleep 即可"

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
__sleep__ = "#sleep"
__wake__ = "#wakeup"
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_cmd_pattern = f"(^{__sleep__})|(^{__wake__})" # (^#setspn)|(^#setnkn)
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def goToSleep(app: Ariadne, message: MessageChain, group: Group, member: Member):
    # 检查是否开启服务
    if(group.id not in config_info["on"]):
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
        return
    message_text = MessageChain(message.get(Plain))
    message_text = str(message_text).replace(' ', '')
    
    # 我要睡觉
    if '#sleep'==str(message):
        if message_text == '#sleep':
            try:
                await app.mute_member(group, member, 6*60*60)
                select_res = random.randint(0,len(config_info["wan_list"])-1)
                await app.send_group_message(group, MessageChain(config_info["wan_list"][select_res]))
            except (PermissionError):
                await app.send_group_message(group, MessageChain('⑨: 咱没权限, 给俺个管理当当?'))
    
    # 睡尼玛，起来嗨
    elif message.has(At):
        # 获取叫醒对象
        member_id = message.get(At)[0].target
        await app.unmute_member(group, member_id)
        # 随机返回图片
        select_res = random.randint(0,len(config_info["return_pic"])-1)
        pic_path=os.path.join(os.path.dirname(__file__), config_info["return_pic"][select_res])
        print("检测存在",os.path.exists(pic_path))
        await app.send_group_message(group, MessageChain([Image(path=pic_path)]))


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