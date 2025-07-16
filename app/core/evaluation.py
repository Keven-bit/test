import asyncio
from subprocess import PIPE, TimeoutExpired
from typing import List, Dict
import os
from ..db.schemas import *
from ..db.database import ASession
from ..core.errors import HTTPException
import psutil
from pathlib import Path
from sqlmodel import select
import time


async def test_code(
    session: ASession, 
    submission_id: int,
    code: str,
    testcases: List[SampleItem],
    language: str,
    time_limit: float = 3.0,
    memory_limit: int = 128,   
    
):
    try:
        case_items: List[Dict] = []
        
        temp_file = None
        temp_exe_file = None
        exec_command = None
        is_successful = True
        pass_count = 0 
        
        # If python, just create py file
        if language == "python":
            temp_file = f"temp_{submission_id}.py"
            exec_command = ["python", temp_file]
            try:
                with open(temp_file, "w") as f:
                    f.write(code)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Server Error: Failed to write python code file.{e}"
                )

        # If C++, create cpp file and compile it to exe file.
        elif language == "C++":
            temp_file = f"temp_{submission_id}.cpp"
            temp_exe_file = f"temp_{submission_id}.exe"
            exec_command = [temp_exe_file]
            
            try:
                # Write code into file
                with open(temp_file, "w") as f:
                    f.write(code)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Server Error: Failed to write C++ code file.{e}"
                )
            
            try:
                compile_proc = await asyncio.create_subprocess_exec(
                    "g++", temp_file, "-o", temp_exe_file,
                    stderr=PIPE
                )
                # Get error in compiling
                complie_stdout, compile_stderr = await compile_proc.communicate()
                
                # Error in compiling
                if compile_proc.returncode != 0:
                    is_successful = False
                    # 测例信息记录（编译错误）
                    case_items.append({
                        "id": 0,
                        "result": "CE",
                        "time": 0.0,
                        "memory": 0
                    })
                    
                    submission_log = SubmissionLog(
                        submission_id=submission_id,
                        details=case_items,
                        score=0,
                        counts=len(testcases) * 10
                    )
                    
                    submission = await session.get(SubmissionItem, submission_id)
                    submission.status = "error"
                    submission.score = 0
                    
                    session.add(submission_log)
                    session.add(submission)
                    await session.commit()
                    return 
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Server Error: C++ compiling failed.{e}"
                )    
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Server Error: Unsupported programming language '{language}'"
            )        
        
                
        # Examine test cases, if python or compiled C++
        for i, case in enumerate(testcases):
            proc = None
            mem_monitor_task = None
            start_time = time.monotonic()
            time_usage = 0.0
            memory_usage = 0
            current_case_result = "UNK"
            try:
                proc = await asyncio.create_subprocess_exec(
                    *exec_command,
                    stdin=PIPE, stdout=PIPE, stderr=PIPE
                )

                # Memory monitor
                if memory_limit > 0:
                    mem_monitor_task = asyncio.create_task(
                        monitor_memory_usage(proc.pid, memory_limit)
                    )
            except Exception as e:
                if proc and proc.returncode is None:
                    proc.kill()
                if mem_monitor_task and not mem_monitor_task.done():
                    mem_monitor_task.cancel()
                    try: await mem_monitor_task
                    except asyncio.CancelledError: pass
                raise HTTPException(
                    status_code=500,
                    detail=f"Server Error: Failed to start code execution / memory monitor.{e}"
                )     

            # Start to capture error in submission code running
            try:
                # Get output and error
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=case["input"].encode()),
                    timeout=time_limit
                )
                # record time usage
                end_time = time.monotonic
                time_usage = end_time - start_time
                
                # If started a mem monitor, cancel it.
                if mem_monitor_task:
                    mem_monitor_task.cancel()
                    try:
                        # Get memort usage
                        memory_usage = await mem_monitor_task
                    except asyncio.CancelledError:
                        pass
                    except MemoryError:
                        # MLE
                        current_case_result = "MLE"
                        
                
                # Judge if output is correct
                output = stdout.decode().strip()
                is_correct = output == case["output"].strip()
                error = stderr.decode().strip() if stderr else None
                
                if error:
                    is_successful = False
                    ### 测例信息记录（运行错误）
                    current_case_result = "RE"
                if not error and is_correct:
                    pass_count += 1
                    ### 测例信息记录(答案是否正确)
                    current_case_result = "AC"
                else:
                    current_case_result = "WA"
            
            except TimeoutExpired:
                proc.kill()
                is_successful = False
                ### 测例信息记录(超时) 
                current_case_result = "TLE"
                time_usage = time_limit
            except MemoryError:
                proc.kill()
                is_successful = False
                ### 测例信息记录（内存超限）
                current_case_result = "MLE"
            except Exception as e:
                is_successful = False 
                current_case_result = "UNK"
                # UNK  
            finally:
                if proc and proc.returncode is None:
                    proc.kill()
                if mem_monitor_task and not mem_monitor_task.done():
                    mem_monitor_task.cancel()
                    try: 
                        memory_usage = await mem_monitor_task
                    except asyncio.CancelledError: 
                        pass
                    
            # Record result of current case
            case_items.append({
                "id": i + 1,
                "result": current_case_result,
                "time": time_usage,
                "memory": memory_usage
            })

        # Judge test result, and update db
        try:
            submission = await session.get(SubmissionItem, submission_id)
            submission.status = "success" if is_successful else "error"
            submission.score = pass_count * 10
            session.add(submission)
            
            # If submission_log already exists (rejudge), update it; or add new one.
            result = await session.execute(
                select(SubmissionLog).where(SubmissionLog.submission_id == submission_id)
            )
            existing_log = result.scalar_one_or_none()
            
            if existing_log:
                existing_log.details=case_items,
                existing_log.score=pass_count * 10
                session.add(existing_log)
            else:
                submission_log = SubmissionLog(
                submission_id=submission_id,
                details=case_items,
                score=pass_count * 10,
                counts=len(testcases) * 10
            )            
                session.add(submission_log)
            
            await session.commit()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Server Error: failed to update submission status in db.{e}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server Error: An unexpected issue occurred during code evaluation.{e}"
        )
    
    # Clean temporary files
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Warning: fail to clean temporary file '{temp_file}':{e}")
            
        if temp_exe_file and os.path.exists(temp_exe_file):
            try:
                os.remove(temp_exe_file)
            except Exception as e:
                print(f"Warning: fail to clean temporary file '{temp_exe_file}':{e}")
        


        
async def monitor_memory_usage(pid: int, memory_limit: int):
    """
    Monitor Memory usage, raise MemoryError if exceed limit
    """
    process = psutil.Process(pid)
    peak_memory_mb = 0.0  # Record peak memory
    try:
        while True:
            mem_info = process.memory_info()
            current_memory_mb = mem_info.rss / (1024 * 1024)
            if current_memory_mb > peak_memory_mb:
                peak_memory_mb = current_memory_mb
                
            if  current_memory_mb > memory_limit:  # Convert to MB
                raise MemoryError(f"Memory limit exceeded ({memory_limit}MB)")
            await asyncio.sleep(0.05)  # Check every 100ms
    except psutil.NoSuchProcess:
        pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in memory monitor for PID {pid}: {e}")
    finally:
        return int(round(peak_memory_mb))