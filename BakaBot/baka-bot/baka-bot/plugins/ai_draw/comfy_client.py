import asyncio
import json
import aiohttp
import websockets
import nonebot
import os
import traceback
from .db import TaskStatus, UserDataDB
from .config import DrawBotConfig
import ast



class FluxClient:
    def __init__(self, botCfg: DrawBotConfig):
        self.server_address = botCfg.server_address
        self.client_id = botCfg.client_id
        self.ws = None
        self.status = "initing"
        self.output_path = botCfg.flux_output_path
        self.db_path = botCfg.db_path
        self.game_name = ""

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
            
    def set_gaming(self, game_name):
        self.game_name = game_name
        self.status = "gaming"
    
    def set_waiting(self):
        self.status = "waiting"
        self.game_name = ""
    
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
                await db.update_task_on_completion(prompt_id, res_img_path) # 下面的发送逻辑很可能失败
                try:
                    bot = nonebot.get_bot()
                    task_info = await db.get_task_by_prompt_id(prompt_id)
                    prompt_dict = ast.literal_eval(task_info['prompt'])
                    seed = prompt_dict['25']['inputs']['noise_seed']

                    if (task_info['group_id'] != task_info['user_id']): # 群组消息
                        await bot.call_api("send_group_msg", 
                                        group_id=task_info['group_id'], 
                                        message=f"[CQ:image,file=file:///{res_img_path}][CQ:at,qq={task_info['user_id']}] seed: {seed}")
                    else: # 私人消息
                        await bot.call_api("send_private_msg", 
                                        user_id=task_info['user_id'], 
                                        message=f"[CQ:image,file=file:///{res_img_path}] seed: {seed}")
                        
                    print(f"debug: 任务完成 {prompt_id}")
                    await db.update_task_on_send(prompt_id)
                except Exception as e: # 打印错误信息 和 traceback
                    print(f"任务完成但发送失败 prompt_id: {prompt_id}, {e}, {traceback.format_exc()}")


    async def connect(self, init = False):
        if (init):
            while True:
                try:
                    bot = nonebot.get_bot()
                    break
                except Exception as e:
                    print("ComfyClient: 等待bot初始化")
                await asyncio.sleep(1)
                

        while True:
            if (self.status == "gaming"):
                print("ComfyClient: 检测到游戏进程, 等待游戏结束")
                await asyncio.sleep(30)
                continue

            try:
                self.ws = await websockets.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
                print("ComfyClient: 连接成功")
                self.status = "running"
                # 先处理未完成消息
                await self.recover()
                # 进入监听循环
                await self.run_recv_loop()

            except (websockets.InvalidStatusCode, ConnectionRefusedError, ConnectionResetError, websockets.exceptions.ConnectionClosedError):
                print("Connection failed. Retrying in 5 seconds...")
                if (self.ws): 
                    await self.ws.close()
                    
                if (self.status == "gaming"):
                    await asyncio.sleep(30)
                    continue

                self.set_waiting()
                await asyncio.sleep(5)

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
            print("ComfyClient: 连接关闭")
    
    async def recover(self):
        async with UserDataDB(self.db_path) as db:
            print("debug: 重新发送中途断开的任务")
            # 先将所有中途断开的任务状态设置为未完成
            await db.reset_in_progress_tasks()
            # 重新发送这些任务
            pending_tasks = await db.get_pending_tasks()
            for task in pending_tasks:
                prompt_dict = ast.literal_eval(task['prompt'])
                add_res = await self.queue_prompt(prompt_dict)
                await db.update_task_on_creation(task['task_uuid'], add_res['prompt_id'])
                print(f"debug: 重新发送任务 user_id: {task['user_id']}, group_id: {task['group_id']}, prompt_id: {add_res['prompt_id']}")
            
            # 重新发送未发送的任务
            not_send_tasks = await db.get_not_send_tasks()
            for task in not_send_tasks:
                prompt_dict = ast.literal_eval(task['prompt'])
                try:
                    bot = nonebot.get_bot()
                    seed = prompt_dict['25']['inputs']['noise_seed']
                    await bot.call_api("send_group_msg", 
                                    group_id=task['group_id'], 
                                    message=f"[CQ:image,file=file:///{task['result_output_path']}][CQ:at,qq={task['user_id']}] 断线恢复1 seed: {seed}")
                    print(f"debug: 重新发送任务结果 user_id: {task['user_id']}, group_id: {task['group_id']}, prompt_id: {task['prompt_id']}")
                    await db.update_task_on_send(task['prompt_id'])
                except Exception as e: # 打印错误信息 和 traceback
                    print(f"任务完成但发送失败 prompt_id: {task['prompt_id']}, {e}, {traceback.format_exc()}")
        