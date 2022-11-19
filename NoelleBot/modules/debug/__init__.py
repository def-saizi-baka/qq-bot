from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.model import Group, Member, Friend
from graia.ariadne.event.mirai import NewFriendRequestEvent
from graia.ariadne.message.element import Image, Plain, At
from graia.ariadne.util.saya import decorate, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex


channel = Channel.current()


channel.meta['name'] = 'Debug'
channel.meta['author'] = ['SaiZi']
channel.meta['description'] = (
    "自动同意好友申请"
)



@listen(NewFriendRequestEvent)
async def main(app: Ariadne, event: NewFriendRequestEvent):
    print("检测到好友请求，自动通过")
    await event.accept()
    # await app.send_group_message(sender_group, MessageChain([At(sender.id), f"Debug: 不要说{str(message)}，来点涩图，test TempMessage"]))
