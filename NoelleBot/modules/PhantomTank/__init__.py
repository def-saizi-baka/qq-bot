import os, json, time, re
from PIL import Image as pltImage
from io import BytesIO

from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.model import Group, Member, Friend
from graia.ariadne.event.message import GroupMessage, FriendMessage, TempMessage
from graia.ariadne.message.element import Image, Plain, At
from graia.ariadne.util.saya import decorate, listen
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex


channel = Channel.current()

channel.meta['name'] = 'PhantomTank'
__name__ = channel.meta['name']
channel.meta['author'] = ['SaiZi']
channel.meta['description'] = (
    "生成欢迎坦克"
)

# 工作路径
work_path = os.path.dirname(__file__)

# 指令相关
re_cmd_pattern = u"^\s*#tank\s*(\d+)"
__OPEN__ = f"#open {channel.meta['name']}"
__CLOSE__ = f"#close {channel.meta['name']}"
re_switch_pattern = f"({__OPEN__})|({__CLOSE__})"

# 打开配置文件
config_path = os.path.join(work_path,"config.json")
config_info = {}
with open(config_path, 'r', encoding='utf-8') as f:
    config_info = json.load(f)

# 该模块的工作数组, key为用户qq号，val为群号
serve_group = {}


@listen(FriendMessage)
@decorate(MatchRegex(regex=re_cmd_pattern, full=False))
async def main(app: Ariadne, sender: Friend, message: MessageChain):
    re_eng = re.compile(re_cmd_pattern)
    group_id = int((re_eng.findall(str(message)))[0])
    # 判断开关
    if(group_id not in config_info["on"]):
        await app.send_friend_message(sender, MessageChain([f" 该服务暂未在该群开启, 请在该群里发送\n{__OPEN__}\n 开启服务"]))
        return

    # 解析指令，添加到工作队列, 为用户添加工作路径
    serve_group[sender.id] = group_id
    user_path = os.path.join(work_path, str(sender.id))
    if not os.path.exists(user_path):
        os.mkdir(user_path)
    
    await app.send_friend_message(sender, MessageChain("请发送图片"))



@listen(FriendMessage)
async def makePhoto(app: Ariadne, sender: Friend, message: MessageChain):
    # 检查有无图片
    if not message.has(Image):
        return 
    # 遍历工作数组查找
    user_id = -1
    for key in serve_group.keys():
        if(key == sender.id):
            user_id = key

    # 得到用户所在群组
    if user_id != -1:
        user_group = serve_group[user_id]
    else:
        return

    if(len(serve_group.keys())<=1):
        await app.send_friend_message(sender, MessageChain("图片制作中, 请稍等"))
    else:
        await app.send_friend_message(sender, MessageChain([f"图片制作中, 请稍等, 当前等候任务数量为: {len(serve_group.keys())-1}"]))

    # 获取用户图片并保存到目录
    user_data = message.get(Image)[0]
    user_data = await user_data.get_bytes()
    user_img = pltImage.open(BytesIO(user_data))
    user_path = os.path.join(work_path, str(user_id), "source.png")
    user_img.save(user_path)

    # 制作幻影坦克
    res_path = colorful_shio(12, 7, user_path)

    # 发送数据
    await app.send_group_message(user_group, MessageChain(["#From: ", At(sender.id), Image(path=res_path)]))
    # 返回信息
    await app.send_friend_message(sender, MessageChain("制作完毕, 请查看对应群有无图片信息"))
    
    # 删除图片
    os.remove(user_path)
    os.remove(res_path)

    # 删除数组
    del serve_group[user_id]


def colorful_shio(brightness_f, brightness_b, data_path):
    '''给定两个参数调整里外图亮度以求得最佳幻坦效果'''
    start=time.time()
    image_f=pltImage.open(os.path.join(work_path, 'f.jpg'))
    image_b=pltImage.open(data_path)
    #导出宽高信息
    w_f,h_f=image_f.size
    w_b,h_b=image_b.size
    #注意：jep图片的像素信息储存格式为RGB，缺少透明度的设置
    #所以需要新建一个RGBA格式的照片文件
    w_min=min(w_f,w_b)
    h_min=min(h_f,h_b)
    new_image=pltImage.new('RGBA',(w_min,h_min))#此处使用的是两者较大一方的参数
    #load()将图片的像素信息储存成array，提供位置坐标即可调出
    # 其速度优于open()
    array_f=image_f.load()
    array_b=image_b.load()
    #调整为同比例图片（计算宽高比例）
    scale_h_f=int(h_f/h_min)
    scale_w_f=int(w_f/w_min)
    scale_h_b=int(h_b/h_min)
    scale_w_b=int(w_b/w_min)
    #确定较小的比例为参照比例
    scale_f=min(scale_h_f,scale_w_f)
    scale_b=min(scale_h_b,scale_w_b)
    #使选中像素点居于原图片中央
    trans_f_x=int((w_f-w_min*scale_f)/2)
    trans_b_x=int((w_b-w_min*scale_b)/2)
    #设置修正参数
    #待选值有：10-8，11-7，11-8
    #均为实验所得 格式为a-b
    a=brightness_f
    b=brightness_b
    for i in range(0,w_min):
        for j in range(0,h_min):
            #注意：像素点位置是修正过的
            R_f,G_f,B_f=array_f[trans_f_x+i*scale_f,j*scale_f]
            R_b,G_b,B_b=array_b[trans_b_x+i*scale_b,j*scale_b]
            #对亮度信息进行修正
            R_f *= a/10
            R_b *= b/10
            G_f *= a/10
            G_b *= b/10
            B_f *= a/10
            B_b *= b/10
            #注意：下面的系数变量及结果通过LAB颜色空间求颜色近似度得到
            delta_r = R_b - R_f
            delta_g = G_b - G_f
            delta_b = B_b - B_f
            coe_a = 8+255/256+(delta_r - delta_b)/256
            coe_b = 4*delta_r + 8*delta_g + 6*delta_b + ((delta_r - delta_b)*(R_b+R_f))/256 + (delta_r**2 - delta_b**2)/512
            A_new = 255 + coe_b/(2*coe_a)
            A_new = int(A_new)
            #A_new可能存在不属于0-255的情况，需要进行修正
            if A_new<=0:
                A_new=0
                R_new=0
                G_new=0
                B_new=0
            elif A_new>=255:
                A_new=255
                R_new=int((255*(R_b)*b/10)/A_new)
                G_new=int((255*(G_b)*b/10)/A_new)
                B_new=int((255*(B_b)*b/10)/A_new)
            else:
                A_new=A_new
                R_new=int((255*(R_b)*b/10)/A_new)
                G_new=int((255*(G_b)*b/10)/A_new)
                B_new=int((255*(B_b)*b/10)/A_new)
            pixel_new=(R_new,G_new,B_new,A_new)
            #注：刚发现调试是可以看到临时数据的，需要设置断点
            # print(pixel_new)
            #导入像素信息
            new_image.putpixel((i,j),pixel_new)
    #保存比特流
    res_path = os.path.join(os.path.dirname(data_path), "data.png")
    new_image.save(res_path)
    #计算运行程序总时间
    end=time.time()
    print('running time:%ds'%(end-start))
    return res_path





# 模块开关
@listen(GroupMessage)
@decorate(MatchRegex(regex=re_switch_pattern))
async def moduleSwitch(app: Ariadne, message: MessageChain, group: Group):
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