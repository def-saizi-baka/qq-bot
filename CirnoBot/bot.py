from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Group, MiraiSession

app = Ariadne(
            MiraiSession(
                        host="http://localhost:8080",
                                verify_key="1146012601",
                                        account=1146012601,
                                                # 此处的内容请按照你的 MAH 配置来填写
        ),
)
bcc = app.broadcast


@bcc.receiver(FriendMessage)
async def setu(app: Ariadne, sender: Friend, message: MessageChain):
    await app.sendFriendMessage(Friend, MessageChain.create(
                    f"botest"
    ))

app.launch_blocking()
