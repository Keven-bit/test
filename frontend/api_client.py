import httpx
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000/api"

async def call_api(method: str, path: str, json_data: dict = None, headers: dict = None, params: dict = None):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=f"{API_BASE_URL}{path}",
                json=json_data,
                headers=headers,
                params=params,
                timeout=30
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

async def login_user(username: str, password: str):
    response = await call_api("POST", "/auth/login", json_data={"username": username, "password": password})
    if response and response.get("code") == 200:
        st.session_state.username = response["data"]["username"]
        st.session_state.user_id = response["data"]["user_id"]
        st.session_state.role = response["data"]["role"]
        st.success("Login successful!")
        return True
    elif response:
        st.error(f"Login failed: {response.get('msg', 'Unknown error')}")
    return False

async def get_problems_list():
    response = await call_api("GET", "/problems/")
    if response and response.get("code") == 200:
        return response["data"]
    return []

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

async def get_submission_log(submission_id: str):
    response = await call_api("GET", f"/submissions/{submission_id}/log")
    if response and response.get("code") == 200:
        return response["data"]
    return None

async def get_supported_languages():
    response = await call_api("GET", "/languages/")
    if response and response.get("code") == 200:
        return [lang["name"] for lang in response["data"]]
    return ["python", "java", "cpp"]

async def logout_user():
    response = await call_api("POST", "/auth/logout")
    if response and response.get("code") == 200:
        st.success("Logout successful!")
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


async def add_problem(problem_data: dict):
    # 后端添加题目接口需要登录，并依赖 check_login_and_get_user
    # 通常，添加题目操作会进一步限制为管理员权限，这里假设API依赖已经处理
    response = await call_api("POST", "/problems/", json_data=problem_data)
    if response and response.get("code") == 200:
        st.success(f"Problem '{response['data']['title']}' added successfully with ID: {response['data']['id']}")
        return True
    elif response:
        st.error(f"Failed to add problem: {response.get('msg', 'Unknown error')}")
    return False
