import json
import os
import re
import mido
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Quote, Plain, Voice
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.util.saya import decorate, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex
from graiax import silkcoder
# 插件信息
__name__ = "乐谱创作"
__description__ = "发送简谱, 编译为语音"
__author__ = "saizi"
__usage__ = "加群"
__cammand__ = "#sheet"


channel = Channel.current()
channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

# 打开配置文件
base_path = os.path.dirname(__file__)
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

# 正则匹配
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_cmd_pattern = "^#sheet\s+(bpm\s*=\s*\d+)?"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"


@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def create_sheet(app: Ariadne, message: MessageChain, group: Group):
    if(group.id not in config_info["on"]):
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送{__OPEN__}开启服务"))
        return
    # 仅获取文字部分
    message_text = str(MessageChain(message.get(Plain)))
    res = await geneate_wav(message_text)
    if(res):
        audio_bytes = await silkcoder.async_encode(base_path+"/output.wav", ios_adaptive=True)
        await app.send_group_message(group, MessageChain(Voice(data_bytes=audio_bytes)))
    else:
        await app.send_group_message(group, MessageChain("⑨: 解析乐谱失败"))
    # 解析命令

# 一个八度
EIGHT_TONE = 12

# MIDDLE_C
MIDDLE_C = 60

# 应付偏移量
ToneOffset = {
    "0": -1,
    "1": 0,
    "2": 2,
    "3": 4,
    "4": 5,
    "5": 7,
    "6": 9,
    "7": 11
}
def getToneNum(tone: str,eight_offset: str, up_lower: str)->int:
    # 假如用户输入了8...
    err_offset = int(tone)//8
    if(err_offset > 0):
        tone = str(int(tone)%8+1)
    if(ToneOffset[tone]==-1):
        return -1

    # 基准音
    res = ToneOffset[tone] + MIDDLE_C

    # 计算八度偏移
    eight_offset_num = len(eight_offset)
    if(eight_offset_num!=0) and eight_offset[0]=='-':
        eight_offset_num*=-1
    res += (eight_offset_num+err_offset)*EIGHT_TONE

    # 计算升降符号
    up_lower_tag = len(up_lower)
    if(up_lower_tag!=0 and up_lower[0]=='b'):
        up_lower_tag*=-1
    res += up_lower_tag

    return res


async def geneate_wav(cmd_str: str)->bool:
    ''' 生成wav文件, 返回是否生成成功 '''
    # 获取音符
    tone_match = re.compile(r'(\+*|\-*)(\d)(#|b)?')
    # 获取Bpm
    get_bpm_pattern = re.compile(r'bpm\s*=\s*(\d+)')
    # 读取Bpm
    bpm = get_bpm_pattern.search(cmd_str)
    if(bpm == None):
        bpm = 120
        print("缺少Bpm, 设为默认值")
    else:
        sub = get_bpm_pattern.search(cmd_str).group(0)
        bpm = int(get_bpm_pattern.search(cmd_str).group(1))
        cmd_str=cmd_str.replace(sub, "")
    
    # 设置速度, 音色
    tempo = 6*(10**7)//bpm
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # 乐器, 速度
    track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(mido.MetaMessage('track_name', name='Piano 1', time=0))
    track.append(mido.Message('program_change', program=1, time=0))  # 这个音轨使用的乐器

    # 读取音符
    tone_list = tone_match.findall(cmd_str)
    tone_num_list = []
    for tone in tone_list:
        eight_str = tone[0]
        tone_data = tone[1]
        uplow_tag = tone[2]
        tone_num_list.append(getToneNum(tone_data, eight_str, uplow_tag))
        # 音符
    if(len(tone_num_list) == 0):
        return False

    # 添加音符到音轨
    for i in range(len(tone_num_list)):
        if(tone_num_list[i] == -1):
            continue

        else:
            meta_time = 60 * 60 * 10 // bpm
            # 获取音符长度
            index = i+1
            while(index < len(tone_num_list) and tone_num_list[index] == -1):
                index+=1
            tone_lengh = index - i
            if tone_num_list[i]>= MIDDLE_C:
                track.append(mido.Message('note_on', note=tone_num_list[i] , velocity=64+20*(tone_num_list[i]-MIDDLE_C)//12, time=0))
                track.append(mido.Message('note_off', note=tone_num_list[i] , velocity=64+20*(tone_num_list[i]-MIDDLE_C)//12, time=meta_time*tone_lengh))
            else:
                track.append(mido.Message('note_on', note=tone_num_list[i] , velocity=64, time=0))
                track.append(mido.Message('note_off', note=tone_num_list[i] , velocity=64, time=meta_time*tone_lengh))
    from midi2audio import FluidSynth
    s = FluidSynth(sound_font="test.sf2")
    mid.save(base_path+'/a1.mid')
    s.midi_to_audio(base_path+'/a1.mid', base_path+'/output.wav')
    return True


# 模块开关
@listen(GroupMessage)
@decorate(MatchRegex(regex=re_switch_pattern))
async def moduleswitch(app: Ariadne, message: MessageChain, group: Group):
    cmd = str(message)
    group_id = group.id
    # 开启指令
    if(cmd == __OPEN__):
        if(group_id in config_info['on']):
            await app.send_group_message(
                group_id, MessageChain(f" {__name__} 已经开启啦")
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