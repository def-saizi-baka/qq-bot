#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
识别群内的B站链接、分享、av号、BV号并获取其对应的视频的信息

以下几种消息均可触发

 - 新版B站app分享的两种小程序
 - 旧版B站app分享的xml消息
 - B站概念版分享的json消息
 - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/{av/bv号} （m.bilibili.com 也可以
 - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap
 - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap
 - BV1xx411c7mD
 - av2
"""

import re
import time
import urllib
import os, json
from base64 import b64encode
from dataclasses import dataclass
from io import BytesIO
from typing import Literal

from graia.amnesia.builtins.aiohttp import AiohttpClientInterface
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graiax.text2img.playwright.builtin import template2img
from graiax.text2img.playwright.types import PageParms
from launart import Launart
from loguru import logger
from PIL.Image import Image as PILImage
from qrcode import QRCode
from graia.ariadne.util.saya import decorate, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex

from .util.control.interval import ManualInterval
from .util.fonts_provider import fill_font
from .util.path import root_path

channel = Channel.current()

channel.meta['name'] = 'B站解析'
channel.meta['author'] = ['Red_lnn']
channel.meta['description'] = (
    '识别群内的B站链接、分享、av号、BV号并获取其对应的视频的信息\n'
    '以下几种消息均可触发：\n'
    ' - 新版B站app分享的两种小程序\n'
    ' - 旧版B站app分享的xml消息\n'
    ' - B站概念版分享的json消息\n'
    ' - 文字消息里含有B站视频地址，如 https://www.bilibili.com/video/{av/bv号} （m.bilibili.com 也可以）\n'
    ' - 文字消息里含有B站视频地址，如 https://b23.tv/3V31Ap\n'
    ' - 文字消息里含有BV号，如 BV1xx411c7mD\n'
    ' - 文字消息里含有av号，如 av2'
)

avid_re = '(av|AV)(\\d{1,12})'
bvid_re = '[Bb][Vv]1([0-9a-zA-Z]{2})4[1y]1[0-9a-zA-Z]7([0-9a-zA-Z]{2})'

base_path = os.path.dirname(__file__)

config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
# 打开配置文件
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

__name__ = config_info['name']
__OPEN__ = f"#open {__name__}"
__CLOSE__ = f"#close {__name__}"

re_cmd_pattern = r"(.*bilibili)|(.*b23)|(.*BV)|(.*av)"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

@dataclass
class VideoInfo:
    cover_url: str  # 封面地址
    bvid: str  # BV号
    avid: int  # av号
    title: str  # 视频标题
    sub_count: int  # 视频分P数
    pub_timestamp: int  # 视频发布时间（时间戳）
    upload_timestamp: int  # 视频上传时间（时间戳，不一定准确）
    desc: str  # 视频简介
    duration: int  # 视频长度（单位：秒）
    up_mid: int  # up主mid
    up_name: str  # up主名称
    up_face: str  # up主头像地址
    views: int  # 播放量
    danmu: int  # 弹幕数
    likes: int  # 点赞数
    coins: int  # 投币数
    replys: int  # 评论数
    favorites: int  # 收藏量


@listen(GroupMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def main(app: Ariadne, group: Group, message: MessageChain, member: Member):
    # 不在白名单, 返回
    if group.id not in config_info['on']:
        print("检测到bilibili链接, 但解析模块未开启")
        return
    print("开始解析b站链接")

    p = re.compile(f'({avid_re})|({bvid_re})')
    msg_str = message.as_persistent_string()
    if 'b23.tv/' in msg_str:
        msg_str = await b23_url_extract(msg_str)
        if not msg_str:
            return
    video_id = p.search(msg_str)
    if not video_id or video_id is None:
        return
    video_id = video_id.group()

    rate_limit, remaining_time = ManualInterval.require(f'{group.id}_{member.id}_bilibiliVideoInfo', 5, 2)
    if not rate_limit:
        await app.send_message(group, MessageChain(Plain(f'冷却中，剩余{remaining_time}秒，请稍后再试')))
        return

    video_info = await get_video_info(video_id)
    if video_info['code'] == -404:
        return await app.send_message(group, MessageChain(Plain('视频不存在')))
    elif video_info['code'] != 0:
        error_text = f'解析B站视频 {video_id} 时出错👇\n错误代码：{video_info["code"]}\n错误信息：{video_info["message"]}'
        logger.error(error_text)
        return await app.send_message(group, MessageChain(Plain(error_text)))
    else:
        video_info = await info_json_dump(video_info['data'])
        print(video_info)
        
        png_path = os.path.join(base_path, './temp.png')
        urllib.request.urlretrieve(video_info.cover_url , filename=png_path)
        # img: bytes = await gen_img(video_info)
        await app.send_message(
            group,
            MessageChain(
                Image(path=png_path),
                Plain(
                    f'{video_info.title}\n'
                    '—————————————\n'
                    f'UP主：{video_info.up_name}\n'
                    f'{math(video_info.views)}播放 {math(video_info.likes)}赞\n'
                    f'链接：https://b23.tv/{video_info.bvid}'
                ),
            ),
        )

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

async def b23_url_extract(b23_url: str) -> Literal[False] | str:
    url = re.search(r'b23.tv[/\\]+([0-9a-zA-Z]+)', b23_url)
    if url is None:
        return False

    launart = Launart.current()
    session = launart.get_interface(AiohttpClientInterface).service.session

    async with session.get(f'https://{url.group()}', allow_redirects=True) as resp:
        target = str(resp.url)
    return target if 'www.bilibili.com/video/' in target else False


async def get_video_info(video_id: str) -> dict:
    launart = Launart.current()
    session = launart.get_interface(AiohttpClientInterface).service.session

    if video_id[:2].lower() == 'av':
        async with session.get(f'http://api.bilibili.com/x/web-interface/view?aid={video_id[2:]}') as resp:
            return await resp.json()
    elif video_id[:2].lower() == 'bv':
        async with session.get(f'http://api.bilibili.com/x/web-interface/view?bvid={video_id}') as resp:
            return await resp.json()
    return {}


async def info_json_dump(obj: dict) -> VideoInfo:
    return VideoInfo(
        cover_url=obj['pic'],
        bvid=obj['bvid'],
        avid=obj['aid'],
        title=obj['title'],
        sub_count=obj['videos'],
        pub_timestamp=obj['pubdate'],
        upload_timestamp=obj['ctime'],
        desc=obj['desc'].strip(),
        duration=obj['duration'],
        up_mid=obj['owner']['mid'],
        up_name=obj['owner']['name'],
        up_face=obj['owner']['face'],
        views=obj['stat']['view'],
        danmu=obj['stat']['danmaku'],
        likes=obj['stat']['like'],
        coins=obj['stat']['coin'],
        replys=obj['stat']['reply'],
        favorites=obj['stat']['favorite'],
    )


def math(num: int):
    if num < 10000:
        return str(num)
    elif num < 100000000:
        return ('%.2f' % (num / 10000)) + '万'
    else:
        return ('%.2f' % (num / 100000000)) + '亿'

