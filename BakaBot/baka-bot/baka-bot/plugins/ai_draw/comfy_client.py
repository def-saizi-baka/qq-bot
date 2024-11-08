import asyncio
import json
import aiohttp
import websockets
import nonebot


class FluxClient:
    def __init__(self, server_address, client_id):
        self.server_address = server_address
        self.client_id = client_id
        self.ws = None
        self.status = "initing"

    async def queue_prompt(self, prompt):
        """ 添加绘制任务
        """
        async with aiohttp.ClientSession() as session:
            p = {"prompt": prompt, "client_id": self.client_id}
            data = json.dumps(p).encode('utf-8')
            async with session.post(f"http://{self.server_address}/prompt", data=data) as response:
                print(f"debug: 添加绘制任务 {response.json()}")
                return await response.json()
    
    async def run_recv_loop(self):
        while True:
            async for out in self.ws:
                self.handle_message(out)

    def handle_message(self, out):
        """ 处理ws收到的消息
        """
        if (not isinstance(out, str)):
            return
        
        message = json.loads(out)
        # 暂时只打印调试信息
        if message['type'] != "crystools.monitor":
            print(f'recv data: {message}')
            

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