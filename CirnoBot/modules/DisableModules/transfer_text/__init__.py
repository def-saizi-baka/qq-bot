import json
import os
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# 插件信息
__name__ = "transfer_text"
__description__ = "翻译"
__author__ = "saizi"
__usage__ = "在群内发送配置文件中给定的口令"

channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

config_info = {}


# 打开配置文件
# 配置文件格式为：
# {
#     "ask":str,
#     "ans":str
# }
def get_transfer(text: str, lang: str) -> str:
    from google_trans_new import google_translator
    translator = google_translator(timeout=10)  # 实例化翻译对象
    # 进行第一次翻译，目标是韩文
    translations = translator.translate(text, lang)
    # 获得翻译结果
    return translations


current_path = os.path.dirname(__file__)
with open(current_path + '/config.json', 'r', encoding='utf-8') as f:
    config_info = json.load(f)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def check_alive(app: Ariadne, message: MessageChain, sender: Member,
                      group: Group):
    # 开头存在指令
    if message.asDisplay()[0:len(config_info['cmd'])] == config_info['cmd']:
        print("检测到指令")
        # 按照语言缩写字符长度命名
        lang_5 = message.asDisplay()[len(config_info['cmd']) + 1:len(config_info['cmd']) + 6]
        lang_2 = lang_5[0:2]
        lang_3 = lang_5[0:3]
        lang = ''  # 语言统一参数
        respond_str = [At(sender.id), Plain('\n')]
        if lang_2 in config_info['lang'].keys():
            lang = lang_2
        if lang_3 in config_info['lang'].keys():
            lang = lang_3
        if lang_5 in config_info['lang'].keys():
            lang = lang_5
        print(f"检测到语言{lang}")
        # 进行翻译
        if len(lang) != 0:
            print(f"开始翻译")
            # 进行转化
            try:
                transfer_str = message.asDisplay()[len(config_info['cmd']) + 1 + len(lang):]
                print(f'翻译串为：{transfer_str}')
                respond_str.append(Plain(get_transfer(transfer_str, lang)))
            except:
                import traceback, sys
                traceback.print_exc()  # 打印异常信息
                exc_type, exc_value, exc_traceback = sys.exc_info()
                error = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
                respond_str = error
        else:
            respond_str.append(Plain("暂时不支持该种语言"))

        #     回复结果
        await app.sendGroupMessage(
            group, MessageChain.create(respond_str))
