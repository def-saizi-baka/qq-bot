import aiosqlite
from enum import IntEnum
import uuid


# 定义任务状态的枚举
class TaskStatus(IntEnum):
    NOT_CREATED = 0  # 任务未创建的状态
    IN_PROGRESS = 1  # 任务正在进行状态
    COMPLETED = 2    # 任务已完成
    COMPLETED_NOT_SEND = 3  # 任务已完成但未发送

# 定义用于处理用户数据的数据库类
class UserDataDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_conn = None  # 数据库连接

    # 实现异步上下文管理器
    async def __aenter__(self):
        self.db_conn = await aiosqlite.connect(self.db_path)
        await self.initialize()  # 确保数据库已初始化
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.db_conn.close()

    # 初始化数据库，创建数据表
    async def initialize(self):
        await self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS user_tasks (
                task_uuid TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                prompt_id TEXT,
                status INTEGER NOT NULL,
                config_path TEXT,
                result_output_path TEXT
            )
        ''')
        await self.db_conn.commit()
    
    async def insert_user_task(self, user_id, group_id, prompt):
        task_uuid = str(uuid.uuid4())  # 生成UUID
        await self.db_conn.execute('''
            INSERT INTO user_tasks (task_uuid, user_id, group_id, prompt, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (task_uuid, user_id, group_id, prompt, TaskStatus.NOT_CREATED))
        await self.db_conn.commit()
        return task_uuid

    
    # 当任务创建成功后，更新队列ID和状态
    async def update_task_on_creation(self, task_uuid, prompt_id):
        await self.db_conn.execute('''
            UPDATE user_tasks
            SET prompt_id = ?,
                status = ?
            WHERE task_uuid = ?
        ''', (prompt_id, TaskStatus.IN_PROGRESS, task_uuid))
        await self.db_conn.commit()
    
    # 当任务完成时，更新状态和结果输出路径
    async def update_task_on_completion(self, prompt_id, result_output_path):
        await self.db_conn.execute('''
            UPDATE user_tasks
            SET status = ?,
                result_output_path = ?
            WHERE prompt_id = ?
        ''', (TaskStatus.COMPLETED_NOT_SEND, result_output_path, prompt_id))
        await self.db_conn.commit()
    
    # 成功发送时，更新任务状态
    async def update_task_on_send(self, prompt_id):
        await self.db_conn.execute('''
            UPDATE user_tasks
            SET status = ?
            WHERE prompt_id = ?
        ''', (TaskStatus.COMPLETED, prompt_id))
        await self.db_conn.commit()

    async def get_task_by_prompt_id(self, prompt_id):
        async with self.db_conn.execute('''
            SELECT task_uuid, user_id, group_id
            FROM user_tasks
            WHERE prompt_id = ?
        ''', (prompt_id,)) as cursor:
            task = await cursor.fetchone()
            return {
                'task_uuid': task[0],
                'user_id': task[1],
                'group_id': task[2]
            }
    
    
    # 在特殊情况下，重置正在进行的任务
    async def reset_in_progress_tasks(self):
        await self.db_conn.execute('''
            UPDATE user_tasks
            SET status = ?,
                prompt_id = NULL
            WHERE status = ?
        ''', (TaskStatus.NOT_CREATED, TaskStatus.IN_PROGRESS))
        await self.db_conn.commit()
    
    # 获取所有未创建的任务，以便重新创建
    async def get_pending_tasks(self):
        async with self.db_conn.execute('''
            SELECT task_uuid, user_id, group_id, prompt
            FROM user_tasks
            WHERE status = ?
        ''', (TaskStatus.NOT_CREATED,)) as cursor:
            tasks = await cursor.fetchall()
            return tasks

