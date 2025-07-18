import streamlit as st
import asyncio
import io

from api_client import (
    login_user,
    get_problem_list,
    add_problem,
    delete_problem,
    get_problem_details,
    submit_code,
    get_submission_result,
    get_submission_list,
    rejudge,
    register_language,
    get_supported_languages,
    logout_user,
    register_user,
    get_users_list,
    update_role,
    get_submission_log,
    set_log_visibility,
    get_log_access_list,
    reset_system,
    export_data,
    import_data,
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
    st.title("在线判题系统 登录")

    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("登录"):
            success = await login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.current_page = "main_app"
                st.rerun()
    with col2:
        if st.button("注册"):
            st.session_state.current_page = "register"
            st.rerun()

async def register_page():
    st.title("注册新账号")

    new_username = st.text_input("新用户名")
    new_password = st.text_input("新密码", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("创建账号"):
            if new_username and new_password:
                success = await register_user(new_username, new_password)
                if success:
                    st.session_state.current_page = "login"
                    st.rerun()
            else:
                st.warning("用户名和密码不能为空。")
    with col2:
        if st.button("返回登录"):
            st.session_state.current_page = "login"
            st.rerun()

async def main_app():
    st.sidebar.title(f"欢迎, {st.session_state.username}!")
    st.sidebar.write(f"您的角色: {st.session_state.role}")

    if st.sidebar.button("注销"):
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

    tab_titles = ["题目", "提交", "评测历史"]
    if st.session_state.role == "admin":
        tab_titles.extend(["管理", "系统"])

    tabs = st.tabs(tab_titles)

    with tabs[0]:
        st.header("题目列表")

        problems = await get_problem_list()
        
        if problems:
            problem_titles = {p["title"]: p["id"] for p in problems}
            selected_title = st.selectbox("选择题目", list(problem_titles.keys()))
            
            if selected_title:
                st.session_state.selected_problem_id = problem_titles[selected_title]

                problem_details = await get_problem_details(st.session_state.selected_problem_id)
                if problem_details:
                    st.subheader(problem_details.get("title", "题目详情"))
                    st.write(f"**题目 ID:** `{problem_details.get('id', 'N/A')}`")
                    st.write(f"**描述:** {problem_details.get('description', 'N/A')}")
                    st.write(f"**输入说明:** {problem_details.get('input_description', 'N/A')}")
                    st.write(f"**输出说明:** {problem_details.get('output_description', 'N/A')}")
                    if "samples" in problem_details and problem_details["samples"]:
                        st.write("**示例:**")
                        for i, sample in enumerate(problem_details["samples"]):
                            st.code(f"输入:\n{sample.get('input', '')}\n输出:\n{sample.get('output', '')}", language="text")
                    st.write(f"**约束:** {problem_details.get('constraints', 'N/A')}")
                    st.write(f"**时间限制:** {problem_details.get('time_limit', 'N/A')} 秒")
                    st.write(f"**内存限制:** {problem_details.get('memory_limit', 'N/A')} MB")
                    st.write(f"**难度:** {problem_details.get('difficulty', 'N/A')}")
                else:
                    st.warning("加载题目详情失败。")
            else:
                st.warning("未选择题目。")
        else:
            st.info("暂无可用题目。")

        st.markdown("---")
        with st.expander("添加新题目"):
            st.subheader("新题目详情")
            problem_id = st.text_input("题目 ID", key="add_problem_id_input")
            title = st.text_input("标题", key="add_problem_title_input")
            description = st.text_area("描述", key="add_problem_description_input")
            input_description = st.text_area("输入说明", key="add_problem_input_desc_input")
            output_description = st.text_area("输出说明", key="add_problem_output_desc_input")

            st.write("示例 (输入/输出对)")
            sample_input = st.text_area("示例输入", key="add_sample_input")
            sample_output = st.text_area("示例输出", key="add_sample_output")
            samples = []
            if sample_input and sample_output:
                samples.append({"input": sample_input, "output": sample_output})

            constraints = st.text_input("约束", key="add_constraints_input")

            st.write("测试用例 (输入/输出对)")
            testcase_input = st.text_area("测试用例输入", key="add_testcase_input")
            testcase_output = st.text_area("测试用例输出", key="add_testcase_output")
            testcases = []
            if testcase_input and testcase_output:
                testcases.append({"input": testcase_input, "output": testcase_output})

            hint = st.text_input("提示 (可选)", key="add_hint_input")
            source = st.text_input("来源 (可选)", key="add_source_input")
            tags_str = st.text_input("标签 (逗号分隔, 可选)", key="add_tags_input")
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            
            time_limit = st.number_input("时间限制 (秒)", min_value=0.1, value=1.0, step=0.1, key="add_time_limit_input")
            memory_limit = st.number_input("内存限制 (MB)", min_value=1, value=128, step=1, key="add_memory_limit_input")
            author = st.text_input("作者 (可选)", key="add_author_input")
            difficulty = st.selectbox("难度", ["", "简单", "中等", "困难"], key="add_difficulty_select")

            public_cases = st.checkbox("公开测试用例 (在日志中显示详细信息)", value=False, key="add_public_cases_checkbox")

            if st.button("提交新题目", key="submit_new_problem_button"):
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
                    "public_cases": public_cases
                }
                if not all([problem_id, title, description, input_description, output_description, constraints]):
                    st.warning("请填写所有必填字段 (ID, 标题, 描述, 输入/输出说明, 约束)。")
                elif not samples:
                    st.warning("请至少提供一个示例输入/输出对。")
                elif not testcases:
                    st.warning("请至少提供一个测试用例输入/输出对。")
                else:
                    success = await add_problem(new_problem_data)
                    if success:
                        st.session_state.selected_problem_id = problem_id
                        st.rerun()

    with tabs[1]:
        st.header("代码提交")

        if st.session_state.selected_problem_id:
            supported_languages = ["python", "C++"]
            language = st.selectbox("选择语言", supported_languages)
            code = st.text_area("在此处输入您的代码", height=300)

            if st.button("提交代码"):
                if code.strip() == "":
                    st.warning("代码不能为空！")
                else:
                    st.session_state.current_submission_id = await submit_code(st.session_state.selected_problem_id, language, code)
                    if st.session_state.current_submission_id:
                        st.rerun()
        else:
            st.info("请先选择一个题目才能提交代码。")

    with tabs[2]:
        st.header("评测历史")

        # 详细提交结果部分 (由 current_submission_id 控制显示)
        if st.session_state.current_submission_id:
            st.subheader(f"提交 ID: `{st.session_state.current_submission_id}` 的结果")
            
            submission_result = await get_submission_result(st.session_state.current_submission_id)

            if submission_result:
                st.write(f"**状态:** {submission_result.get('status', '未知')}")
                st.write(f"**分数:** {submission_result.get('score', 'N/A')}")
                st.write(f"**总分:** {submission_result.get('counts', 'N/A')}")

                if st.button("查看评测日志详情", key="view_log_button"):
                    log_data = await get_submission_log(st.session_state.current_submission_id)
                    if log_data and "details" in log_data:
                        st.write("**详细评测结果:**")
                        st.dataframe(log_data["details"])
                    else:
                        st.info("详细日志不可用或权限不足。")

                if submission_result.get('status') in ['pending', 'judging']:
                    st.info("评测进行中，请刷新查看最新结果...")
                    if st.button("刷新结果", key="refresh_result_button"):
                        st.rerun()
                else:
                    st.success("评测完成！")
            else:
                st.warning("未能获取提交结果。评测可能正在进行或提交 ID 无效。")
                if st.button("刷新结果", key="refresh_result_button_fallback"):
                    st.rerun()
            
            st.markdown("---")
            if st.button("返回评测历史列表", key="back_to_history_list_button"):
                st.session_state.current_submission_id = None
                st.rerun()
        else:
            # 评测历史列表部分
            st.subheader("评测历史列表")
            
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                filter_user_id = st.text_input("按用户 ID 筛选 (管理员专属)", value=st.session_state.user_id if st.session_state.role != "admin" else "", disabled=(st.session_state.role != "admin"), key="filter_user_id")
            with filter_col2:
                all_problems_for_filter = await get_problem_list()
                problem_filter_options = {"所有题目": None}
                if all_problems_for_filter:
                    problem_filter_options.update({p["title"]: p["id"] for p in all_problems_for_filter})
                selected_problem_filter_title = st.selectbox("按题目筛选", list(problem_filter_options.keys()), key="filter_problem_id")
                filter_problem_id = problem_filter_options[selected_problem_filter_title]
            with filter_col3:
                filter_status = st.selectbox("按状态筛选", ["所有状态", "pending", "success", "error"], key="filter_status")
                if filter_status == "所有状态":
                    filter_status = None
            
            st.subheader("分页")
            page = st.number_input("页码", min_value=1, value=1, step=1, key="page_number")
            page_size = st.number_input("每页条目数", min_value=1, value=10, step=1, key="page_size")

            submission_list_data = await get_submission_list(
                user_id=filter_user_id if st.session_state.role == "admin" else st.session_state.user_id,
                problem_id=filter_problem_id,
                status=filter_status,
                page=page,
                page_size=page_size
            )

            if submission_list_data and submission_list_data["submissions"]:
                # 仅展示提交ID、状态、分数、总分
                display_submissions = []
                for s in submission_list_data["submissions"]:
                    display_submissions.append({
                        "提交 ID": s.get("submission_id", "N/A"), # 使用 .get() 方法
                        "评测状态": s.get("status", "N/A"), # 使用 .get() 方法
                        "分数": s.get("score", "N/A"), # 使用 .get() 方法
                        "总分": s.get("counts", "N/A") # 使用 .get() 方法
                    })
                
                st.write(f"总提交数: {submission_list_data['total']}")
                
                edited_df = st.data_editor(
                    display_submissions,
                    key="submission_history_editor",
                    hide_index=True,
                    column_order=["提交 ID", "评测状态", "分数", "总分"],
                    column_config={
                        "提交 ID": st.column_config.TextColumn("提交 ID", help="点击查看详细日志"),
                        "评测状态": st.column_config.TextColumn("评测状态"),
                        "分数": st.column_config.NumberColumn("分数"),
                        "总分": st.column_config.NumberColumn("总分"),
                    },
                    num_rows="dynamic",
                    use_container_width=True
                )

                selected_rows = [row for row in edited_df if row.get('_selected', False)]
                if selected_rows:
                    selected_submission_id_from_list = selected_rows[0]["提交 ID"]
                    if st.button(f"查看选中提交 `{selected_submission_id_from_list}` 的日志", key="view_selected_log_button"):
                        st.session_state.current_submission_id = selected_submission_id_from_list
                        st.rerun()
                else:
                    st.info("请从列表中选择一个提交以查看其日志。")

            else:
                st.info("未找到符合条件的提交。")


    if st.session_state.role == "admin":
        with tabs[3]:
            st.header("管理功能")

            with st.expander("删除题目"):
                st.subheader("删除现有题目")
                
                all_problems = await get_problem_list()
                if all_problems:
                    problem_titles_map = {p["title"]: p["id"] for p in all_problems}
                    delete_selected_title = st.selectbox("选择要删除的题目", list(problem_titles_map.keys()), key="delete_problem_select")
                    
                    if delete_selected_title:
                        delete_problem_id = problem_titles_map[delete_selected_title]
                        st.write(f"要删除的题目 ID: `{delete_problem_id}`")
                        if st.button("确认删除", key="confirm_delete_problem_button"):
                            success = await delete_problem(delete_problem_id)
                            if success:
                                st.session_state.selected_problem_id = None
                                st.rerun()
                    else:
                        st.info("没有可删除的题目。")
                else:
                    st.info("未找到可删除的题目。")

            st.markdown("---")
            with st.expander("重新评测提交"):
                st.subheader("重新评测现有提交")
                
                rejudge_submission_list_data = await get_submission_list(page_size=100)
                
                if rejudge_submission_list_data and rejudge_submission_list_data["submissions"]:
                    rejudge_options = {f"ID: {s['submission_id']} (题目: {s['problem_id']}, 状态: {s['status']})": s["submission_id"] for s in rejudge_submission_list_data["submissions"]}
                    selected_rejudge_option = st.selectbox("选择要重新评测的提交", list(rejudge_options.keys()), key="rejudge_submission_select")
                    
                    if selected_rejudge_option:
                        submission_id_to_rejudge = rejudge_options[selected_rejudge_option]
                        st.write(f"要重新评测的提交 ID: `{submission_id_to_rejudge}`")
                        if st.button("确认重新评测", key="confirm_rejudge_button"):
                            success = await rejudge(submission_id_to_rejudge)
                            if success:
                                st.session_state.current_submission_id = submission_id_to_rejudge
                                st.rerun()
                    else:
                        st.info("没有可重新评测的提交 (或获取失败)。")
                else:
                    st.info("未找到可重新评测的提交。")

            st.markdown("---")
            with st.expander("注册新语言"):
                st.subheader("语言详情")
                lang_name = st.text_input("语言名称 (例如, python, C++)", key="reg_lang_name_input")
                lang_file_ext = st.text_input("文件扩展名 (例如, .py, .cpp)", key="reg_lang_ext_input")
                lang_compile_cmd = st.text_input("编译命令 (可选, 例如, g++ {filename} -o {output_file})", key="reg_lang_compile_cmd_input")
                lang_run_cmd = st.text_input("运行命令 (例如, python {filename}, ./a.out)", key="reg_lang_run_cmd_input")
                lang_time_limit = st.number_input("默认时间限制 (秒, 可选)", min_value=0.1, value=None, step=0.1, key="reg_lang_time_limit_input")
                lang_memory_limit = st.number_input("默认内存限制 (MB, 可选)", min_value=1, value=None, step=1, key="reg_lang_memory_limit_input")

                if st.button("注册语言", key="register_language_button"):
                    if not lang_name or not lang_file_ext or not lang_run_cmd:
                        st.warning("语言名称、文件扩展名和运行命令是必填项。")
                    else:
                        success = await register_language(
                            name=lang_name,
                            file_ext=lang_file_ext,
                            compile_cmd=lang_compile_cmd if lang_compile_cmd else None,
                            run_cmd=lang_run_cmd,
                            time_limit=lang_time_limit if lang_time_limit is not None else None,
                            memory_limit=lang_memory_limit if lang_memory_limit is not None else None
                        )
                        if success:
                            st.rerun()

            st.markdown("---")
            with st.expander("更新用户角色"):
                st.subheader("更改用户角色")
                
                all_users_data = await get_users_list(page_size=100)
                if all_users_data and all_users_data["users"]:
                    user_options = {f"ID: {u['user_id']} | 用户名: {u['username']} (当前角色: {u['role']})": u["user_id"] for u in all_users_data["users"]}
                    selected_user_to_update = st.selectbox("选择用户", list(user_options.keys()), key="update_user_select")
                    
                    if selected_user_to_update:
                        target_user_id = user_options[selected_user_to_update]
                        
                        available_roles = ["admin", "user", "banned"] 
                        new_role = st.selectbox("选择新角色", available_roles, key="new_role_select")
                        
                        st.write(f"用户 ID: `{target_user_id}`")
                        st.write(f"选择的新角色: `{new_role}`")

                        if st.button("确认更新角色", key="confirm_update_role_button"):
                            success = await update_role(target_user_id, new_role)
                            if success:
                                st.rerun()
                    else:
                        st.info("没有可更新的用户 (或获取失败)。")
                else:
                    st.info("未找到可更新的用户。")

            st.markdown("---")
            with st.expander("用户列表"):
                st.subheader("查看所有用户")
                
                user_list_page = st.number_input("页码", min_value=1, value=1, step=1, key="user_list_page_number")
                user_list_page_size = st.number_input("每页用户数", min_value=1, value=10, step=1, key="user_list_page_size")

                all_users_for_display = await get_users_list(page=user_list_page, page_size=user_list_page_size)

                if all_users_for_display and all_users_for_display["users"]:
                    st.write(f"总用户数: {all_users_for_display['total']}")
                    st.dataframe(all_users_for_display["users"])
                else:
                    st.info("系统中没有用户。")
                
                if st.button("刷新用户列表", key="refresh_user_list_button"):
                    st.rerun()


    if st.session_state.role == "admin":
        with tabs[4]: # Tabs 索引 4 为管理员“系统”页
            st.header("系统管理")

            with st.expander("配置题目日志可见性"):
                st.subheader("设置公开测试用例可见性")
                
                all_problems_for_visibility = await get_problem_list()
                if all_problems_for_visibility:
                    problem_visibility_map = {p["title"]: p["id"] for p in all_problems_for_visibility}
                    selected_problem_visibility_title = st.selectbox("选择题目", list(problem_visibility_map.keys()), key="log_visibility_problem_select")
                    
                    if selected_problem_visibility_title:
                        problem_id_to_configure = problem_visibility_map[selected_problem_visibility_title]
                        
                        current_problem_details = await get_problem_details(problem_id_to_configure)
                        current_public_cases = current_problem_details.get('public_cases', False) if current_problem_details else False

                        new_public_cases_status = st.checkbox(f"设为公开 (当前: {current_public_cases})", value=current_public_cases, key="public_cases_checkbox")
                        
                        if st.button("设置可见性", key="set_visibility_button"):
                            success = await set_log_visibility(problem_id_to_configure, new_public_cases_status)
                            if success:
                                st.rerun()
                    else:
                        st.info("没有可配置日志可见性的题目。")
                else:
                    st.info("未找到可配置日志可见性的题目。")

            st.markdown("---")
            with st.expander("审计日志访问"):
                st.subheader("查看日志访问记录")
                
                log_audit_user_id = st.text_input("按用户 ID 筛选 (可选)", key="log_audit_user_id_input")
                log_audit_problem_id = st.text_input("按题目 ID 筛选 (可选)", key="log_audit_problem_id_input")
                log_audit_page = st.number_input("页码", min_value=1, value=1, step=1, key="log_audit_page_number")
                log_audit_page_size = st.number_input("每页记录数", min_value=1, value=10, step=1, key="log_audit_page_size")

                audit_list_data = await get_log_access_list(
                    user_id=log_audit_user_id if log_audit_user_id else None,
                    problem_id=log_audit_problem_id if log_audit_problem_id else None,
                    page=log_audit_page,
                    page_size=log_audit_page_size
                )

                if audit_list_data and audit_list_data["logs"]:
                    st.write(f"总审计记录: {audit_list_data['total']}")
                    st.dataframe(audit_list_data["logs"])
                else:
                    st.info("未找到符合条件的审计日志。")
                
                if st.button("刷新审计日志", key="refresh_audit_logs_button"):
                    st.rerun()

            st.markdown("---")
            with st.expander("系统重置"):
                st.subheader("重置所有数据")
                st.warning("警告: 这将删除所有用户数据、题目、提交和日志。此操作无法撤销。")
                if st.button("确认系统重置", key="confirm_system_reset_button"):
                    success = await reset_system()
                    if success:
                        st.session_state.current_page = "login"
                        st.rerun()

            st.markdown("---")
            with st.expander("数据导入/导出"):
                st.subheader("导出所有数据")
                if st.button("导出数据", key="export_data_button"):
                    exported_data = await export_data()
                    if exported_data:
                        st.json(exported_data)
                        st.download_button(
                            label="下载导出数据",
                            data=str(exported_data),
                            file_name="exported_oj_data.json",
                            mime="application/json",
                            key="download_export_button"
                        )

                st.subheader("导入数据")
                st.warning("警告: 导入数据可能会覆盖现有数据或创建重复项 (取决于后端逻辑)。")
                uploaded_file = st.file_uploader("上传 JSON 文件", type=["json"], key="import_file_uploader")
                if uploaded_file is not None:
                    if st.button("从文件导入数据", key="import_data_button"):
                        file_content = uploaded_file.read()
                        success = await import_data(file_content)
                        if success:
                            st.rerun()


async def run_app():
    if st.session_state.current_page == "login":
        await login_page()
    elif st.session_state.current_page == "register":
        await register_page()
    elif st.session_state.current_page == "main_app":
        if not st.session_state.logged_in:
            st.session_state.current_page = "login"
            st.rerun()
        else:
            await main_app()

if __name__ == "__main__":
    asyncio.run(run_app())
