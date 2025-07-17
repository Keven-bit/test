import streamlit as st
import asyncio
from api_client import (
    login_user, get_problems_list, submit_code, get_submission_result,
    get_supported_languages, logout_user, register_user, get_problem_details,
    get_submission_log
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"
if "current_submission_id" not in st.session_state:
    st.session_state.current_submission_id = None
if "selected_problem_id" not in st.session_state:
    st.session_state.selected_problem_id = None

async def login_page():
    st.title("Online Judge System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            success = await login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.current_page = "main_app"
                st.rerun()
    with col2:
        if st.button("Register"):
            st.session_state.current_page = "register"
            st.rerun()

async def register_page():
    st.title("Register New Account")

    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Account"):
            if new_username and new_password:
                success = await register_user(new_username, new_password)
                if success:
                    st.session_state.current_page = "login"
                    st.rerun()
            else:
                st.warning("Username and password cannot be empty.")
    with col2:
        if st.button("Back to Login"):
            st.session_state.current_page = "login"
            st.rerun()

async def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.write(f"Your role: {st.session_state.role}")

    if st.sidebar.button("Logout"):
        success = await logout_user()
        if success:
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.role = None
            st.session_state.current_page = "login"
            st.session_state.current_submission_id = None
            st.session_state.selected_problem_id = None
            st.rerun()

    st.title("Problem List")

    problems = await get_problems_list()
    
    if problems:
        problem_titles = {p["title"]: p["id"] for p in problems}
        selected_title = st.selectbox("Select a Problem", list(problem_titles.keys()))
        
        if selected_title:
            st.session_state.selected_problem_id = problem_titles[selected_title]

            problem_details = await get_problem_details(st.session_state.selected_problem_id)
            if problem_details:
                st.subheader(problem_details.get("title", "Problem Details"))
                st.write(f"**Problem ID:** `{problem_details.get('id', 'N/A')}`")
                st.write(f"**Description:** {problem_details.get('description', 'N/A')}")
                st.write(f"**Input Description:** {problem_details.get('input_description', 'N/A')}")
                st.write(f"**Output Description:** {problem_details.get('output_description', 'N/A')}")
                if "samples" in problem_details and problem_details["samples"]:
                    st.write("**Samples:**")
                    for i, sample in enumerate(problem_details["samples"]):
                        st.code(f"Input:\n{sample.get('input', '')}\nOutput:\n{sample.get('output', '')}", language="text")
                st.write(f"**Constraints:** {problem_details.get('constraints', 'N/A')}")
                st.write(f"**Time Limit:** {problem_details.get('time_limit', 'N/A')} seconds")
                st.write(f"**Memory Limit:** {problem_details.get('memory_limit', 'N/A')} MB")
                st.write(f"**Difficulty:** {problem_details.get('difficulty', 'N/A')}")
            else:
                st.warning("Failed to load problem details.")
        else:
            st.warning("No problem selected.")
    else:
        st.info("No problems available yet.")

    st.markdown("---")
    st.header("Submit Code")

    if st.session_state.selected_problem_id:
        supported_languages = await get_supported_languages()
        language = st.selectbox("Select Language", supported_languages)
        code = st.text_area("Enter your code here", height=300)

        if st.button("Submit Code"):
            if code.strip() == "":
                st.warning("Code cannot be empty!")
            else:
                st.session_state.current_submission_id = await submit_code(st.session_state.selected_problem_id, language, code)
                if st.session_state.current_submission_id:
                    st.rerun()
    else:
        st.info("Please select a problem to submit code.")

    st.markdown("---")
    st.header("Submission Results")

    if st.session_state.current_submission_id:
        st.write(f"Querying result for Submission ID: `{st.session_state.current_submission_id}`...")
        
        submission_result = await get_submission_result(st.session_state.current_submission_id)

        if submission_result:
            st.write(f"**Status:** {submission_result.get('status', 'Unknown')}")
            st.write(f"**Score:** {submission_result.get('score', 'N/A')}")
            st.write(f"**Total Counts:** {submission_result.get('counts', 'N/A')}")

            if submission_result.get('status') in ['pending', 'judging']:
                st.info("Evaluation in progress. Please refresh for the latest result...")
                if st.button("Refresh Result"):
                    st.rerun()
            else:
                st.success("Evaluation completed!")
                log_data = await get_submission_log(st.session_state.current_submission_id)
                if log_data and "details" in log_data:
                    st.write("**Detailed Evaluation Results:**")
                    st.dataframe(log_data["details"])
                else:
                    st.info("Detailed log not available or permission denied.")
        else:
            st.warning("Failed to retrieve submission result. Evaluation might be pending or ID invalid.")
            if st.button("Refresh Result"):
                st.rerun()
    else:
        st.info("You haven't submitted any code yet.")

async def run_app():
    if st.session_state.current_page == "login":
        await login_page()
    elif st.session_state.current_page == "register":
        await register_page()
    elif st.session_state.current_page == "main_app":
        if not st.session_state.logged_in: # Fallback if session state somehow gets out of sync
            st.session_state.current_page = "login"
            st.rerun()
        else:
            await main_app()

if __name__ == "__main__":
    asyncio.run(run_app())
    
    
if st.session_state.role == "admin": # 只有管理员才能看到此选项
        st.markdown("---")
        with st.expander("Add New Problem"):
            st.subheader("New Problem Details")
            problem_id = st.text_input("Problem ID")
            title = st.text_input("Title")
            description = st.text_area("Description")
            input_description = st.text_area("Input Description")
            output_description = st.text_area("Output Description")

            # 示例部分，你可以添加多个示例输入/输出对
            st.write("Samples (Input/Output Pairs)")
            sample_input = st.text_area("Sample Input", key="sample_input")
            sample_output = st.text_area("Sample Output", key="sample_output")
            samples = []
            if sample_input and sample_output:
                samples.append({"input": sample_input, "output": sample_output})

            constraints = st.text_input("Constraints")

            # 测试用例部分，你可以添加多个测试用例输入/输出对
            st.write("Testcases (Input/Output Pairs)")
            testcase_input = st.text_area("Testcase Input", key="testcase_input")
            testcase_output = st.text_area("Testcase Output", key="testcase_output")
            testcases = []
            if testcase_input and testcase_output:
                testcases.append({"input": testcase_input, "output": testcase_output})

            hint = st.text_input("Hint (Optional)")
            source = st.text_input("Source (Optional)")
            tags_str = st.text_input("Tags (comma-separated, Optional)")
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            
            time_limit = st.number_input("Time Limit (seconds)", min_value=0.1, value=1.0, step=0.1)
            memory_limit = st.number_input("Memory Limit (MB)", min_value=1, value=128, step=1)
            author = st.text_input("Author (Optional)")
            difficulty = st.selectbox("Difficulty", ["", "Easy", "Medium", "Hard"]) # 假设有这些难度级别

            public_cases = st.checkbox("Public Cases (Show test case details in log)", value=False) # 对应 LogVisibility 的 public_cases

            if st.button("Submit New Problem"):
                new_problem_data = {
                    "id": problem_id,
                    "title": title,
                    "description": description,
                    "input_description": input_description,
                    "output_description": output_description,
                    "samples": samples,
                    "constraints": constraints,
                    "testcases": testcases,
                    "hint": hint,
                    "source": source,
                    "tags": tags,
                    "time_limit": time_limit,
                    "memory_limit": memory_limit,
                    "author": author,
                    "difficulty": difficulty,
                    "public_cases": public_cases # 这是 ProblemItem 上的字段，会用于 LogVisibility 的创建
                }
                # 检查必填字段
                if not all([problem_id, title, description, input_description, output_description, constraints]):
                    st.warning("Please fill in all required fields (ID, Title, Description, Input/Output Description, Constraints).")
                elif not samples:
                    st.warning("Please provide at least one sample input/output pair.")
                elif not testcases:
                    st.warning("Please provide at least one testcase input/output pair.")
                else:
                    success = await add_problem(new_problem_data)
                    if success:
                        st.session_state.selected_problem_id = problem_id # 如果添加成功，可以默认选中新添加的题目
                        st.experimental_rerun() # 重新加载题目列表
