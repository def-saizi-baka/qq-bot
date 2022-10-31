import os, json, re
import requests, urllib
from bs4 import BeautifulSoup as bs4
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.model import Group, Member, Friend
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.util.saya import decorate, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex


channel = Channel.current()

channel.meta['name'] = '网易云链接解析'
channel.meta['author'] = ['SaiZi']
channel.meta['description'] = (
    "识别网易云链接"
)

# 配置文件部分
base_path = os.path.dirname(__file__)
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
# 打开配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

# 组件开关
__name__ = config_info['name']
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

url_pattern = re.compile(r'((https://)?music.163.com(/#)?/song\?id=\d+)')
url_m_pattern = re.compile(r'(https://)?y.music.163.com/m/song/(\d+)')
fakeHeaders = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"}



@listen(GroupMessage)
async def main(app: Ariadne, group: Group, message: MessageChain):
    # if group.id not in config_info['on']:
    #     await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送{__OPEN__}开启服务"))
    #     return
    message_text = str(MessageChain(message.get(Plain)))
    # 获取url
    find_res = url_pattern.findall(message_text)
    find_m_res = url_m_pattern.findall(message_text)
    # 匹配URL
    if len(find_res) != 0:
        url = find_res[0][0]
        song_id = re.compile("id=(\d+)").findall(url)[0]
    elif len(find_m_res) != 0:
        song_id = find_m_res[0][1]
    else:
        return
    
    # 获取歌曲id
    if group.id not in config_info['on']:
        await app.send_group_message(group, MessageChain(f"该服务暂未开启, 请发送 {__OPEN__} 开启服务"))
        return
    
    res_dict = await getMusicInfo(song_id)
    print(song_id, res_dict)
    await app.send_group_message(
        group,
        MessageChain(
            Image(path=res_dict["cover_url"]),
            Plain(f"\n歌曲名: {res_dict['歌曲名']}"),
            Plain(f"\n上传名: {res_dict['上传名']}"),
            Plain(f"\n歌曲mv: {res_dict['歌曲mv']}"),
            Plain(f"\n{res_dict['作者']}"),
            Plain(f"\n歌曲链接: {res_dict['url']}")
        )
    )

async def getMusicInfo(song_id)->dict:
    res_dict = {
        "歌曲名":"",
        "上传名":"",
        "歌曲mv":"",
        "作者":"",
    }
    url = f"https://music.163.com/song?id={song_id}&from=qq"
    res_dict["url"] = url
    res = requests.get(url=url, headers=fakeHeaders, timeout=20).content
    soup = bs4(res, "lxml")
    # 获取图片url
    cover_url = soup.find(class_="j-img")['src']
    png_path = os.path.dirname(__file__)+"/temp_cover.png"
    urllib.request.urlretrieve(cover_url , filename=png_path)
    res_dict["cover_url"] = png_path

    # 标题
    title_info = soup.find(class_="hd").find(class_="tit")

    title_name_ele = title_info.find(class_ = "f-ff2")
    if(title_name_ele != None):
        res_dict["歌曲名"] = title_name_ele.text

    title_name_ele = title_info.find(class_ = "subtit f-fs1 f-ff2")
    if(title_name_ele != None):
        res_dict["上传名"] = title_name_ele.text

    title_name_ele = title_info.find('a')
    if(title_name_ele != None):
        res_dict["歌曲mv"] = "https://music.163.com" + title_name_ele["href"]


    # 专辑, 作者
    composer = ""
    for ele in soup.findAll(class_="des s-fc4"):
        composer += f"{ele.text}\n"
    if(len(composer) > 0):
        composer = composer.strip('\n')
        res_dict["作者"] = composer

    return res_dict





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