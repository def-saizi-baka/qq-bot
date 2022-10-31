from PIL import Image as IMG
from PIL import ImageOps
from moviepy.editor import ImageSequenceClip as imageclip
import numpy
import aiohttp
from io import BytesIO
import os, json

from graia.ariadne.app import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At
from graia.ariadne.message.element import Image
from graia.ariadne.exception import AccountMuted
from graia.ariadne.event.message import GroupMessage

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

from graia.ariadne.util.saya import decorate, dispatch, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex

# 插件信息
__name__ = "PetPet"
__description__ = "生成摸头gif"
__author__ = "SAGIRI-kawaii"
__usage__ = "在群内发送 摸@目标 即可"

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
__CMD__ = "摸"
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_cmd_pattern = f"^{__CMD__}"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def petpet_generator(app: Ariadne, message: MessageChain, group: Group):

    if message.has(At):
        # 检查是否开启服务
        if(group.id not in config_info["on"]):
            await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
            return

        if not os.path.exists("./modules/PetPet/temp"):
            os.mkdir("./modules/PetPet/temp")
        await petpet(message.get(At)[0].target)
        try:
            await app.send_group_message(
                group,
                MessageChain([
                    Image(path=f"./modules/PetPet/temp/tempPetPet-{message.get(At)[0].target}.gif")
                ])
            )
        except AccountMuted:
            pass

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

frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91)
]

squish_factor = [
    (0, 0, 0, 0),
    (-7, 22, 8, 0),
    (-8, 30, 9, 6),
    (-3, 21, 5, 9),
    (0, 0, 0, 0)
]

squish_translation_factor = [0, 20, 34, 21, 0]

frames = tuple([f'./modules/PetPet/PetPetFrames/frame{i}.png' for i in range(5)])


async def save_gif(gif_frames, dest, fps=10):
    """生成 gif

    将输入的帧数据合并成视频并输出为 gif

    参数
    gif_frames: list<numpy.ndarray>
    为每一帧的数据
    dest: str
    为输出路径
    fps: int, float
    为输出 gif 每秒显示的帧数

    返回
    None
    但是会输出一个符合参数的 gif
    """
    clip = imageclip(gif_frames, fps=fps)
    clip.write_gif(dest)  # 使用 imageio
    clip.close()


# 生成函数（非数学意味）
async def make_frame(avatar, i, squish=0, flip=False):
    """生成帧

    将输入的头像转变为参数指定的帧，以供 make_gif() 处理

    参数
    avatar: PIL.Image.Image
    为头像
    i: int
    为指定帧数
    squish: float
    为一个 [0, 1] 之间的数，为挤压量
    flip: bool
    为是否横向反转头像

    返回
    numpy.ndarray
    为处理完的帧的数据
    """
    # 读入位置
    spec = list(frame_spec[i])
    # 将位置添加偏移量
    for j, s in enumerate(spec):
        spec[j] = int(s + squish_factor[i][j] * squish)
    # 读取手
    hand = IMG.open(frames[i])
    # 反转
    if flip:
        avatar = ImageOps.mirror(avatar)
    # 将头像放缩成所需大小
    avatar = avatar.resize((int((spec[2] - spec[0]) * 1.2), int((spec[3] - spec[1]) * 1.2)), IMG.ANTIALIAS)
    # 并贴到空图像上
    gif_frame = IMG.new('RGB', (112, 112), (255, 255, 255))
    gif_frame.paste(avatar, (spec[0], spec[1]))
    # 将手覆盖（包括偏移量）
    gif_frame.paste(hand, (0, int(squish * squish_translation_factor[i])), hand)
    # 返回
    return numpy.array(gif_frame)


async def petpet(member_id, flip=False, squish=0, fps=20) -> None:
    """生成PetPet

    将输入的头像生成为所需的 PetPet 并输出

    参数
    path: str
    为头像路径
    flip: bool
    为是否横向反转头像
    squish: float
    为一个 [0, 1] 之间的数，为挤压量
    fps: int
    为输出 gif 每秒显示的帧数

    返回
    bool
    但是会输出一个符合参数的 gif
    """

    url = f'http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640'
    gif_frames = []
    # 打开头像
    # avatar = Image.open(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            img_content = await resp.read()

    avatar = IMG.open(
        (img_content))

    # 生成每一帧
    for i in range(5):
        gif_frames.append(await make_frame(avatar, i, squish=squish, flip=flip))
    # 输出
    await save_gif(gif_frames, f'./modules/PetPet/temp/tempPetPet-{member_id}.gif', fps=fps)

