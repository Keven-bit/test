import httpx
import streamlit as st
import io

API_BASE_URL = "http://127.0.0.1:8000/api"

initial_client_instance = None

async def call_api(method: str, path: str, json_data: dict = None, files: dict = None, headers: dict = None, params: dict = None):
    # 检查 st.session_state 中是否已存在客户端实例
    if "httpx_client" not in st.session_state:
        st.session_state.httpx_client = httpx.AsyncClient(timeout=None)
    
    client = st.session_state.httpx_client 

    try:
        response = await client.request(
            method=method,
            url=f"{API_BASE_URL}{path}",
            json=json_data,
            files=files,
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        st.error(f"API request failed: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        st.error(f"Network error: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None


async def get_problem_list():
    response = await call_api("GET", "/problems/")
    if response and response.get("code") == 200:
        return response["data"]
    return []


async def add_problem(problem_data: dict):
    response = await call_api("POST", "/problems/", json_data=problem_data)
    if response and response.get("code") == 200:
        st.success(f"Problem '{response['data']['title']}' added successfully with ID: {response['data']['id']}")
        return True
    elif response:
        st.error(f"Failed to add problem: {response.get('msg', 'Unknown error')}")
    return False


async def delete_problem(problem_id: str):
    response = await call_api("DELETE", f"/problems/{problem_id}")
    if response and response.get("code") == 200:
        st.success(f"Problem '{response['data']['title']}' (ID: {response['data']['id']}) deleted successfully.")
        return True
    elif response:
        st.error(f"Failed to delete problem: {response.get('msg', 'Unknown error')}")
    return False


async def get_problem_details(problem_id: str):
    response = await call_api("GET", f"/problems/{problem_id}")
    if response and response.get("code") == 200:
        return response["data"]
    return None

async def submit_code(problem_id: str, language: str, code: str):
    json_data = {
        "problem_id": problem_id,
        "language": language,
        "code": code
    }
    response = await call_api("POST", "/submissions/", json_data=json_data)
    if response and response.get("code") == 200:
        st.success(f"Code submitted! Submission ID: {response['data']['submission_id']}")
        return response["data"]["submission_id"]
    elif response:
        st.error(f"Code submission failed: {response.get('msg', 'Unknown error')}")
    return None

async def get_submission_result(submission_id: str):
    response = await call_api("GET", f"/submissions/{submission_id}")
    if response and response.get("code") == 200:
        return response["data"]
    return None


async def get_submission_list(
    user_id: str = None, problem_id: str = None, status: str = None, page: int = None, page_size: int = None
):
    params = {}
    if user_id:
        params["user_id"] = user_id
    if problem_id:
        params["problem_id"] = problem_id
    if status:
        params["status"] = status
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size
        
    response = await call_api("GET", "/submissions/", params=params)
    if response and response.get("code") == 200:
        return response["data"]
    elif response:
        st.error(f"Failed to fetch submission list: {response.get('msg', 'Unknown error')}")
    return {"total": 0, "submissions": []}


async def rejudge(submission_id: str):
    response = await call_api("PUT", f"/submissions/{submission_id}/rejudge")
    if response and response.get("code") == 200:
        st.success(f"Submission ID: {response['data']['submission_id']} rejudge started!")
        return True
    elif response:
        st.error(f"Failed to rejudge submission: {response.get('msg', 'Unknown error')}")
    return False


async def register_language(
    name: str, file_ext: str, compile_cmd: str = None, run_cmd: str = None,
    time_limit: float = None, memory_limit: int = None
):
    json_data = {
        "name": name,
        "file_ext": file_ext,
        "complie_cmd": compile_cmd if compile_cmd else None,
        "run_cmd": run_cmd,
        "time_limit": time_limit,
        "memory_limit": memory_limit
    }

    response = await call_api("POST", "/languages/", json_data=json_data)
    if response and response.get("code") == 200:
        st.success(f"Language '{response['data']['name']}' registered successfully.")
        return True
    elif response:
        st.error(f"Failed to register language: {response.get('msg', 'Unknown error')}")
    return False


async def get_supported_languages():
    response = await call_api("GET", "/languages/")
    if response and response.get("code") == 200:
        return [lang["name"] for lang in response["data"]]
    return ["python", "cpp"]


async def login_user(username: str, password: str):
    response = await call_api("POST", "/auth/login", json_data={"username": username, "password": password})
    if response and response.get("code") == 200:
        st.session_state.username = response["data"]["username"]
        st.session_state.user_id = response["data"]["user_id"]
        st.session_state.role = response["data"]["role"]
        st.success("Login successful!")
        return True
    elif response:
        st.error(f"Login failed, please try again later: {response.get('msg', 'Unknown error')}")
    return False


async def logout_user():
    response = await call_api("POST", "/auth/logout")
    if response and response.get("code") == 200:
        st.success("Logout successful!")
        if "httpx_client" in st.session_state:
            await st.session_state.httpx_client.aclose()
            del st.session_state.httpx_client
        return True
    elif response:
        st.error(f"Logout failed: {response.get('msg', 'Unknown error')}")
    return False


async def register_user(username: str, password: str):
    response = await call_api("POST", "/users/", json_data={"username": username, "password": password})
    if response and response.get("code") == 200:
        st.success("Registration successful! Please log in.")
        return True
    elif response:
        st.error(f"Registration failed: {response.get('msg', 'Unknown error')}")
    return False


async def get_user(user_id: str):
    response = await call_api("GET", f"/users/{user_id}")
    if response and response.get("code") == 200:
        return response["data"]
    return None


async def update_role(user_id: str, role: str):
    response = await call_api("PUT", f"/users/{user_id}/role", json_data={"role: role"})
    if response and response.get("code") == 200:
        st.success(f"User '{response['data']['user_id']}' role updated to '{response['data']['role']}'.")
        return True
    elif response:
        st.error(f"Failed to update user role: {response.get('msg', 'Unknown error')}")
    return False


async def get_users_list(page: int = None, page_size: int = None):
    params = {}
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size

    response = await call_api("GET", "/users/", params=params)
    if response and response.get("code") == 200:
        return response["data"] # 返回包含 total 和 users 列表的数据
    elif response:
        st.error(f"Failed to fetch user list: {response.get('msg', 'Unknown error')}")
    return {"total": 0, "users": []}


async def get_submission_log(submission_id: str):
    response = await call_api("GET", f"/submissions/{submission_id}/log")
    if response and response.get("code") == 200:
        return response["data"]
    elif response:
        st.error(f"Failed to fetch submission log: {response.get('msg', 'Unknown error')}")
    return None


async def set_log_visibility(problem_id: str, public_cases: bool):
    response = await call_api("PUT", f"/problems/{problem_id}/log_visibility", json_data={"public_cases": public_cases})
    if response and response.get("code") == 200:
        st.success(f"Log visibility for Problem ID: {problem_id} set to Public: {public_cases}.")
        return True
    elif response:
        st.error(f"Failed to set log visibility: {response.get('msg', 'Unknown error')}")
    return False


async def get_log_access_list(user_id: str = None, problem_id: str = None, page: int = None, page_size: int = None):
    params = {}
    if user_id:
        params["user_id"] = user_id
    if problem_id:
        params["problem_id"] = problem_id
    if page:
        params["page"] = page
    if page_size:
        params["page_size"] = page_size

    response = await call_api("GET", "/logs/", params=params)
    if response and response.get("code") == 200:
        return response["data"]
    elif response:
        st.error(f"Failed to fetch log access list: {response.get('msg', 'Unknown error')}")
    return {"total": 0, "logs": []}


async def reset_system():
    response = await call_api("POST", "/reset/")
    if response and response.get("code") == 200:
        st.success("System reset successfully!")
        return True
    elif response:
        st.error(f"Failed to reset system: {response.get('msg', 'Unknown error')}")
    return False


async def export_data():
    response = await call_api("GET", "/export/")
    if response and response.get("code") == 200:
        return response["data"]
    elif response:
        st.error(f"Failed to export data: {response.get('msg', 'Unknown error')}")
    return None


async def import_data(file_content: bytes):
    file_obj = io.BytesIO(file_content)
    files = {"file": ("data.json", file_obj, "application/json")}
    response = await call_api("POST", "/import/", files=files)
    if response and response.get("code") == 200:
        st.success("Data imported successfully!")
        return True
    elif response:
        st.error(f"Failed to import data: {response.get('msg', 'Unknown error')}")
    return False



