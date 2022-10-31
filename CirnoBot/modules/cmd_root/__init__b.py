from urllib import response
from aiohttp import ClientResponseError
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Plain, Quote
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain, Image
from graia.ariadne.event.message import GroupMessage, Group
import os, json
# 插件信息
__name__ = "cmd_root"
__description__ = "撤回,禁言, 踢出, 添加管理员"
__author__ = "SaiZi"
__usage__ = "撤回,禁言, 踢出"

saya = Saya.current()
channel = Channel.current()

channel.name(__name__)
channel.description(f"{__description__}\n使用方法：{__usage__}")
channel.author(__author__)

# 读取配置文件
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
    "config", "cmd_root", "config.json")
config_info = {}

with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

recall_cmd = "/recall"
mute_cmd = "/mute"
unmute_cmd = "/unmute"
kill_cmd = "/kill"
# 管理员登入与登出
log_on_cmd = "/log on"
log_out_cmd = "log out"
# 添加管理员
add_op_cmd = "/add op"
del_op_cmd = "/del op"

administrator = 744870006
log_group = 130560640

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def root_cmd(app: Ariadne, message: MessageChain, group: Group, member: Member):
    if member.id == administrator:
        message_str_list = message.get(Plain)
        message_text = MessageChain.create(message_str_list)
        message_text = (message_text.asDisplay()).replace(' ', '')
        try:
            # /recall
            if message.has(Quote) and message_text == recall_cmd:
                quote_message_id = (message.get(Quote))[0].id
                # 撤回成员信息
                await app.recallMessage(quote_message_id)
                # 撤回本地信息
                await app.recallMessage(message)
            elif message.has(At) :
                target_member = (message.get(At))[0].target
                # /mute min
                if mute_cmd in message_text:
                    message_text = message_text[len(mute_cmd):]
                    print(f"设置禁言时间{message_text}min")
                    mute_time = int(message_text)
                    await app.muteMember(group, target_member, mute_time*60)
                # unmute
                elif unmute_cmd == message_text:
                    print(f"解除禁言{target_member}")
                    await app.unmuteMember(group, target_member)
                # /kick out group
                elif kill_cmd in message_text:
                    print(f"群{group.id}踢出成员{target_member}")
                    await app.kickMember(group, target_member, f"群{group.id}踢出成员{target_member}")

        #debug
        except Exception:
            import traceback, sys
            traceback.print_exc()  # 打印异常信息
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print(f"错误信息为{exc_type}")
            if exc_type == PermissionError:
                await app.sendGroupMessage(group, MessageChain.create("⑨: 群主让我当当?"))
            elif exc_type == ValueError:
                await app.sendGroupMessage(group, MessageChain.create(f"⑨: {exc_type}"))
            else:
                error = "⑨: 未知错误: "
                error += str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
                await app.sendGroupMessage(log_group, MessageChain.create(error))

    else:
        pass


# 撤回函数   
async def cmd_recall(app: Ariadne, message: MessageChain,  group: Group, member: Member):
    # /recall
    response=""
    if message.has(Quote):
        quote_message = (message.get(Quote))[0]
        # 允许撤回自己 / 管理员撤回其他人信息
        if(member.id == quote_message.senderId or member.id in config_info["sudoer"]):
            await app.recallMessage(quote_message.id)
            # 撤回本地信息
            await app.recallMessage(message)
    else:
        response = "未检测到要撤回的信息"
    
    return response

# 管理员登入
async def set_op(app: Ariadne, member: Member):
    response_content = ""
    # 如果在管理员名单
    if member.id in config_info["sudoer"]:
        # 设置为管理
        if member.permission == "MEMBER":
            response_content = f"已给予成员{member.name}管理员权限"
            await app.modifyMemberAdmin(assign=True, member=member)
        else:
            response_content = "该成员已经为管理员"
    # 不在管理员名单
    else:
        response_content = "没有权限"
    
    return response_content

# 管理员登出
async def cancel_op(app: Ariadne, member: Member):
    response_content = ""
    # 如果在管理员名单
    if member.id in config_info["sudoer"]:
        # 设置为管理
        if member.permission != "MEMBER":
            response_content = f"管理员 {member.name} 已注销"
            await app.modifyMemberAdmin(assign=False, member=member)
        else:
            response_content = "该成员不是管理员"
    # 不在管理员名单
    else:
        response_content = "没有权限"
    
    return response_content


# 添加管理员
async def add_sudoer(app: Ariadne, message: MessageChain,  group: Group, member: Member):
    res_str = ""    # 回复语句
    message_str_list = message.get(Plain)
    message_text = MessageChain.create(message_str_list)
    # 去除前后空格与@的字符串
    message_str = (message_text.asDisplay()).strip()
    # 格式化后的字符串等于添加管理员指令 并且 有@ 说明触发了指令
    if(message_str == add_op_cmd and message.has(At)):
        # 判断权限 只有root才能设置
        if member.id in config_info["root"]:
            add_memeber = message.get(At)[0]
            # 进行添加
            if add_memeber.target in config_info["sudoer"]:
                res_str = "该成员已经是管理员"
            else:
                config_info["sudoer"].append(add_memeber.target)
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(config_info))
                res_str = f"用户 {add_memeber.target} 已被设为管理员"
        # 判断权限 只有root才能设置 
        else:
            res_str = "无权限"
    
    return res_str

# 删除管理员
async def del_sudoer(app: Ariadne, message: MessageChain,  group: Group, member: Member):
    res_str = ""    # 回复语句
    message_str_list = message.get(Plain)
    message_text = MessageChain.create(message_str_list)
    # 去除前后空格与@的字符串
    message_str = (message_text.asDisplay()).strip()
    # 格式化后的字符串等于添加管理员指令 并且 有@ 说明触发了指令
    if(message_str == add_op_cmd and message.has(At)):
        # 判断权限 只有root才能设置
        if member.id in config_info["root"]:
            del_memeber = message.get(At)[0]
            # 进行添加
            if del_memeber.target in config_info["sudoer"]:
                res_str = "该成员不是管理员"
            else:
                config_info["sudoer"].remove(del_memeber.target)
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(config_info))
                # 取消管理身份 
                await app.modifyMemberAdmin(assign=False, member=del_memeber.target, group=group)
                res_str = f"用户 {del_memeber.target} 已被取消管理员权限"
        # 判断权限 只有root才能设置 
        else:
            res_str = "无权限"
    
    return res_str