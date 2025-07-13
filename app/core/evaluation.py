import asyncio
from subprocess import PIPE, TimeoutExpired
from typing import List, Dict
import os
from db.schemas import *
from db.database import ASession
from core.errors import HTTPException
import psutil
from pathlib import Path

# 还需要添加语言
async def test_code(
    session: ASession, 
    submission_id: int,
    code: str,
    testcases: List[SampleItem],
    language: str,
    time_limit: float = 0.0,
    memory_limit: int = 0,   
    
):
    temp_file = f"temp_{submission_id}.py"
    try:
        with open(temp_file, "w") as f:
            f.write(code)
        
        is_successful = True
        pass_count = 0
        for case in testcases:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "python", temp_file,
                    stdin=PIPE, stdout=PIPE, stderr=PIPE
                )
                
                mem_monitor_task = None
                if memory_limit > 0:
                    mem_monitor_task = asyncio.create_task(
                        monitor_memory_usage(proc.pid, memory_limit)
                    )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(input=case["input"].encode()),
                        timeout=time_limit
                    )
                    
                    # If started a mem monitor, cancel it.
                    if mem_monitor_task:
                        mem_monitor_task.cancel()
                        try:
                            await mem_monitor_task
                        except asyncio.CancelledError:
                            pass
                    
                    # Judge if output is correct
                    output = stdout.decode().strip()
                    is_correct = output == case["output"].strip()
                    error = stderr.decode().strip() if stderr else None
                    
                    if error:
                        is_successful = False
                        ### 测例信息记录（运行错误） 待补全
                    if not error and is_correct:
                        pass_count += 1
                    ### 测例信息记录(答案是否正确) 待补全
                
                except TimeoutExpired:
                    proc.kill()
                    is_successful = False
                    ### 测例信息记录(超时) 待补全
                except MemoryError:
                    proc.kill()
                    is_successful = False
                    ### 测例信息记录（内存超限）待补全
                    if mem_monitor_task:
                        mem_monitor_task.cancel()
                                
            except Exception as e:
                is_successful = False
            #     raise HTTPException(
            #     status_code=500,
            #     detail=f"Server Error: {e}"  
            # )
    except:
        is_successful = False ### 调试需注意，这里是否要加try except
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    # Judge test result
    submission = await session.get(SubmissionItem, submission_id)
    submission.status = "success" if is_successful else "error"
    submission.score = pass_count*10
    
    session.add(submission)
    await session.commit()
        
        
async def monitor_memory_usage(pid: int, memory_limit: int):
    """
    Monitor Memory usage, raise MemoryError if exceed limit
    """
    process = psutil.Process(pid)
    while True:
        try:
            mem_info = process.memory_info()
            if mem_info.rss / (1024 * 1024) > memory_limit:  # Convert to MB
                raise MemoryError(f"Memory limit exceeded ({memory_limit}MB)")
            await asyncio.sleep(0.1)  # Check every 100ms
        except psutil.NoSuchProcess:
            break