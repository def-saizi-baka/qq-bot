import os, json
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.exception import AccountMuted
from graia.ariadne.event.message import GroupMessage, Group, Member
from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex

from .utils import genImage

# 插件信息
__name__ = "5000zhao"
__description__ = "一个 5000兆円欲しい! style的图片生成器"
__author__ = "SAGIRI-kawaii"
__usage__ = "发送 `#5000 text1/text2` 即可"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}

# 打开配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)


cmd_5000 = "#5000"
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_pattern = f"({__OPEN__})|({__CLOSE__})"

@listen(GroupMessage)
@decorate(DetectPrefix(cmd_5000))
async def pornhub_style_logo_generator(
    app: Ariadne, message: MessageChain, group: Group):
    if(group.id not in config_info["on"]):
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
        return
    try:
        message_text = str(message).strip()
        if message_text.find(cmd_5000) == 0:
            mid = message_text.find('/')
            if mid != -1:
                left_text = " "+message_text[len(cmd_5000):mid].strip()
                right_text = message_text[mid+1:].strip()
                try:
                    try:
                        genImage(word_a=left_text, word_b=right_text).save("./modules/5000zhao/test.png")
                    except TypeError:
                        await app.send_group_message(group, MessageChain([Plain(text="不支持的内容！不要给我一些稀奇古怪的东西！")]))
                        return None
                    await app.send_group_message(group, MessageChain([Image(path="./modules/5000zhao/test.png")]))
                except AccountMuted:
                    pass
            else:
                await app.send_group_message(group, MessageChain([Plain(text="参数非法! 使用格式: #5000 text1/text2")]))
                
    except ValueError:
        try:
            await app.send_group_message(group, MessageChain.create([Plain(text="参数非法! 使用格式: #5000 text1/text2")]))
        except AccountMuted:
            pass




# 模块开关
@listen(GroupMessage)
@decorate(MatchRegex(regex=re_pattern))
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
