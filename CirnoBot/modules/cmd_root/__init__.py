from urllib import response
from aiohttp import ClientResponseError
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.chain import MessageChain, Plain, Quote
from graia.ariadne.model import Group, Member, MemberPerm
from graia.ariadne.message.element import At, Plain, Image, Source
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

# 配置文件初始化
config_path = os.path.join(os.path.dirname(__file__),"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

recall_cmd = "/recall"
mute_cmd = "/mute"
unmute_cmd = "/unmute"
kill_cmd = "/kill"
# 管理员登入与登出
log_on_cmd = "/log on"
log_out_cmd = "/log out"
# 添加管理员
add_op_cmd = "/add op"
del_op_cmd = "/del op"


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def root_cmd(app: Ariadne, message: MessageChain, group: Group, member: Member):
    message_str_list = message.get(Plain)
    # 获取纯文本内容
    message_text = str(MessageChain(message_str_list))
    # 去除前后空格的文本
    message_strip = message_text.strip()
    # 去除所有空格的文本
    message_text = (message_text).replace(' ', '')
    try:
        res_str = "" # 回复语
        # /recall
        if message.has(Quote) and message_strip == recall_cmd:
            res_str = await cmd_recall(app, message, group, member)

        # 管理员登入
        elif message_strip == log_on_cmd:
            res_str = await set_op(app, member)

        # 管理员注销
        elif message_strip == log_out_cmd:
            res_str = await cancel_op(app, member)

        # 添加管理员
        elif message_strip.find(add_op_cmd) == 0 and message.has(At):
            res_str = await add_op(app, message, group, member)

        # 取消管理员
        elif message_strip.find(del_op_cmd) == 0 and message.has(At):
            res_str = await del_op(app, message, group, member)
        
        elif message.has(At) :
            target_member = (message.get(At))[0].target
            # 禁言 /mute min
            if message_text.find(mute_cmd) == 0:
                if member.id not in config_info["op"]:
                    res_str = "无权限"
                else:
                    message_text = message_text[len(mute_cmd):]
                    print(f"设置禁言时间{message_text}min")
                    mute_time = int(message_text)
                    await app.mute_member(group, target_member, mute_time*60)
            # 解除禁言 unmute
            elif message_text.find(unmute_cmd) == 0:
                if member.id not in config_info["op"]:
                    res_str = "无权限"
                else:
                    print(f"解除禁言{target_member}")
                    await app.unmute_member(group, target_member)
            # 踢出群聊 /kick out group
            elif kill_cmd == message_text:
                if member.id not in config_info["op"]:
                    res_str = "无权限"
                else:
                    print(f"群{group.id}踢出成员{target_member}")
                    res_str = f"用户{target_member}已被移出群聊"
                    await app.kick_member(group, target_member, f"群{group.id}踢出成员{target_member}")

        if len(res_str):
            await app.send_group_message(group, MessageChain(res_str))
    
    #debug
    except Exception:
        import traceback, sys
        traceback.print_exc()  # 打印异常信息
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f"错误信息为{exc_type}")
        if exc_type == PermissionError:
            await app.send_group_message(group, MessageChain("⑨: 咱没权限, 要不群主给我当当?"))
        elif exc_type == ValueError:
            await app.send_group_message(group, MessageChain(f"⑨: {exc_type}"))
        else:
            error = "⑨: 未知错误: "
            error += str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))  # 将异常信息转为字符串
            await app.send_group_message(config_info["log_group"], MessageChain(error))


# 撤回函数   
async def cmd_recall(app: Ariadne, message: MessageChain,  group: Group, member: Member):
    # /recall
    response=""
    if message.has(Quote):
        quote_message = (message.get(Quote))[0]
        # 允许撤回自己 / 管理员撤回其他人信息
        if(member.id == quote_message.sender_id or member.id in config_info["op"]):
            await app.recall_message(quote_message.id, group)
            # 撤回本地信息
            await app.recall_message(message.get(Source)[0].id, group)
        else:
            response = "(ᗜˬᗜ): 无权限"
    else:
        response = "未检测到要撤回的信息"
    
    return response

# 管理员登入
async def set_op(app: Ariadne, member: Member):
    response_content = ""
    # 如果在管理员名单
    if member.id in config_info["op"]:
        # 设置为管理
        print(member.permission)
        if member.permission == MemberPerm.Member:
            response_content = f"已给予成员{member.name}管理员权限"
            await app.modify_member_admin(assign=True, member=member)
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
    if member.id in config_info["op"]:
        # 设置为管理
        if member.permission != MemberPerm.Member:
            response_content = f"管理员 {member.name} 已注销"
            await app.modify_member_admin(assign=False, member=member)
        else:
            response_content = "该成员当前不是管理员"
    # 不在管理员名单
    else:
        response_content = "没有权限"
    
    return response_content


# 添加管理员
async def add_op(app: Ariadne, message: MessageChain,  group: Group, member: Member):
    res_str = ""    # 回复语句
    message_str_list = message.get(Plain)
    message_text = MessageChain(message_str_list)
    # 去除前后空格与@的字符串
    message_str = str(message_text).strip()
    # 格式化后的字符串等于添加管理员指令 并且 有@ 说明触发了指令
    if(message_str == add_op_cmd and message.has(At)):
        # 判断权限 只有root才能设置
        if member.id in config_info["administrator"]:
            add_memeber = message.get(At)[0]
            # 进行添加
            if add_memeber.target in config_info["op"]:
                res_str = "该成员已经是管理员"
            else:
                config_info["op"].append(add_memeber.target)
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(config_info))
                res_str = f"用户 {add_memeber.target} 已被设为管理员"
        # 判断权限 只有root才能设置 
        else:
            res_str = "无权限"
    
    return res_str

# 删除管理员
async def del_op(app: Ariadne, message: MessageChain,  group: Group, member: Member):
    res_str = ""    # 回复语句
    message_str_list = message.get(Plain)
    message_text = MessageChain(message_str_list)
    # 去除前后空格与@的字符串
    message_str = (str(message_text)).strip()
    # 格式化后的字符串等于添加管理员指令 并且 有@ 说明触发了指令
    if(message_str == add_op_cmd and message.has(At)):
        # 判断权限 只有root才能设置
        if member.id in config_info["administrator"]:
            del_memeber = message.get(At)[0]
            # 进行添加
            if del_memeber.target not in config_info["op"]:
                res_str = "该成员不是管理员"
            else:
                config_info["op"].remove(del_memeber.target)
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(config_info))
                # 取消管理身份 
                await app.modify_member_admin(assign=False, member=del_memeber.target, group=group)
                res_str = f"用户 {del_memeber.target} 已被取消管理员权限"
        # 判断权限 只有root才能设置 
        else:
            res_str = "无权限"
    
    return res_str