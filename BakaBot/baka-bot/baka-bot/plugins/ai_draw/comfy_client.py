import asyncio
import json
import aiohttp
import websockets
import nonebot
import os
from .db import TaskStatus, UserDataDB
from .config import DrawBotConfig


class FluxClient:
    def __init__(self, botCfg: DrawBotConfig):
        self.server_address = botCfg.server_address
        self.client_id = botCfg.client_id
        self.ws = None
        self.status = "initing"
        self.output_path = botCfg.flux_output_path
        self.db_path = botCfg.db_path

    async def queue_prompt(self, prompt):
        """ 添加绘制任务
        """
        async with aiohttp.ClientSession() as session:
            p = {"prompt": prompt, "client_id": self.client_id}
            data = json.dumps(p).encode('utf-8')
            async with session.post(f"http://{self.server_address}/prompt", data=data) as response:
                res_data = await response.json()
                print(f"debug: 添加绘制任务 {res_data}")
                return res_data
    
    async def run_recv_loop(self):
        while True:
            async for out in self.ws:
                await self.handle_message(out)

    async def handle_message(self, out):
        """ 处理ws收到的消息
        """
        if (not isinstance(out, str)):
            return
        
        message = json.loads(out)
        # 暂时只打印调试信息
        if message['type'] != "crystools.monitor":
            print(f'recv data: {message}')
        '''
        recv data: {'type': 'executed', 'data': {'node': '77', 'display_node': '77', 'output': {'images': [{'filename': 'Flux-img2img-LR_00045_.png', 'subfolder': 
            '', 'type': 'output'}]}, 'prompt_id': '00a49903-a36e-4619-9612-d2b13d499e0d'}}
        '''
        if message['type'] == "executed":
            prompt_id = message['data']['prompt_id']
            filename = message['data']['output']['images'][0]['filename']
            subfolder = message['data']['output']['images'][0]['subfolder']
            res_img_path = os.path.join(self.output_path, subfolder, filename)
            async with UserDataDB(self.db_path) as db:
                await db.update_task_on_completion(prompt_id, res_img_path)
                bot = nonebot.get_bot()
                task_info = await db.get_task_by_prompt_id(prompt_id)
                await bot.call_api("send_group_msg", 
                                   group_id=task_info['group_id'], 
                                   message=f"[CQ:image,file=file:///{res_img_path}]")
                print(f"debug: 任务完成 {prompt_id}")
                await db.update_task_on_send(prompt_id)


    async def connect(self):
        while True:
            try:
                # 当处于stop状态时，不会自动重连, 等待进程监控线程检测到问题后重新拉起 ComfyUI Server
                if (self.status == "stop"):
                    print("ComfyClient: 已停止")
                    await asyncio.sleep(5)
                    continue

                self.status = "starting"
                self.ws = await websockets.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
                print("ComfyClient: 连接成功")
                self.status = "running"
                await self.run_recv_loop()
            except (websockets.InvalidStatusCode, ConnectionRefusedError):
                print("Connection failed. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def close(self):
        if self.ws is not None:
            self.status = "stop"
            await self.ws.close()
            print("ComfyClient: 连接关闭")