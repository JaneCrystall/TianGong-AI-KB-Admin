import os
import tempfile
from datetime import datetime

import pandas as pd
import pytz
import streamlit as st
from supabase import Client, create_client

# from module.file_local import upload_file

# 配置 Streamlit 页面
st.set_page_config(
    page_title="Reports",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="src/static/favicon.ico",
)

if "password_correct" in st.session_state:

    if "has_rerun" not in st.session_state:
        st.session_state.has_rerun = False

    timezone = pytz.timezone("Asia/Shanghai")
    # 初始化 Supabase 客户端
    supabase: Client = create_client(st.secrets.supabase.url, st.secrets.supabase.key)

    @st.cache_data(show_spinner=False, ttl=600)
    def get_total_count(data_version: int):
        try:
            count_response = (
                supabase.table("reports").select("id", count="exact").execute()
            )
            return count_response.count
        except Exception as e:
            st.error(f"Error fetching total count: {e}")
            return 0

    @st.cache_data(show_spinner=False)
    def fetch_data(
        page_number: int,
        page_size: int,
        sort_field: str = None,
        sort_order: str = "asc",
        data_version: int = 0,
    ):
        try:
            query = supabase.table("reports").select(
                "id, title, issuing_organization, release_date, language, url, uploaded_time"
            )

            if sort_field:
                query = query.order(sort_field, desc=(sort_order == "desc"))
            else:
                query = query.order("uploaded_time", desc=True)

            start = (page_number - 1) * page_size
            response = query.limit(page_size).offset(start).execute()
            dataset = pd.DataFrame(response.data)
            dataset["issuing_organization"] = dataset["issuing_organization"].astype(str)
            dataset["release_date"] = pd.to_datetime(
                dataset["release_date"], utc=True
            )
            dataset["uploaded_time"] = pd.to_datetime(
                dataset["uploaded_time"]
            ).dt.tz_convert("Asia/Shanghai")
            return dataset
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame()


    def update_record(id, data):
        try:
            response = (
                supabase.table("reports").update(data).eq("id", id).execute()
            )
            st.success(f"Record with ID {id} updated successfully")
            st.session_state.data_version += 1
        except Exception as e:
            st.error(f"Error updating record: {e}")

    # 初始化 data_version
    if "data_version" not in st.session_state:
        st.session_state.data_version = 0

    # 获取总记录数
    total_count = get_total_count(st.session_state.data_version)

    # 定义列
    columns = [
        "id",
        "title",
        "issuing_organization",
        "release_date",
        "language",
        "url",
        "uploaded_time",
    ]

    with st.sidebar:
        # 顶部菜单：排序选项
        sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=True, index=1)
        if sort == "Yes" and columns:
            sort_field = st.selectbox("Sort By", options=columns)
            sort_direction = st.radio(
                "Direction", options=["⬆️ Ascending", "⬇️ Descending"], horizontal=True
            )
            sort_order = "asc" if sort_direction == "⬆️ Ascending" else "desc"
        else:
            sort_field = None
            sort_order = "asc"

        # 底部菜单：分页控制
    bottom_menu = st.columns((4, 1, 1))
    with bottom_menu[2]:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("Page Size")
        with col2:
            batch_size = st.selectbox(
                "Page Size",
                label_visibility="collapsed",
                options=[25, 50, 100],
                index=0,
            )
    with bottom_menu[1]:
        total_pages = max(1, (total_count + batch_size - 1) // batch_size)
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("Page")
        with col2:
            current_page = st.number_input(
                "Page",
                label_visibility="collapsed",
                min_value=1,
                max_value=total_pages,
                step=1,
                value=1,
            )
    with bottom_menu[0]:
        st.markdown(f"Page **{current_page}** of **{total_pages}**")

    # 获取当前页面的数据
    dataset = fetch_data(
        page_number=current_page,
        page_size=batch_size,
        sort_field=sort_field,
        sort_order=sort_order,
        data_version=st.session_state.data_version,
    )


    # 显示数据编辑器
    edited_data = st.data_editor(
        data=dataset,
        disabled=["id"],  # 使 'id' 列只读
        use_container_width=True,
        num_rows="dynamic",
        height=400,
        key="data_editor",
        column_config={
            "url": st.column_config.LinkColumn(display_text="Open file"),
            "effective_date": st.column_config.DateColumn(),
            "expiration_date": st.column_config.DateColumn(),
            "last_updated_time": st.column_config.DatetimeColumn(
                format="YYYY-MM-DD HH:mm:ss", disabled=True
            ),
            "uploaded_time": st.column_config.DatetimeColumn(
                format="YYYY-MM-DD HH:mm:ss", disabled=True
            ),
        },
    )


    with st.expander("Upload File for Selected Record"):
        # 构建选项列表
        record_options = dataset["id"].astype(str) + " - " + dataset["title"]

        # Wrap upload logic in a separate form
        with st.form("upload_form"):
            selected_record = st.selectbox("Select a record", options=record_options)
            uploaded_file = st.file_uploader(
                "Upload a file", type=["pdf", "docx", "txt"]
            )

            upload_submitted = st.form_submit_button("Upload File")

            if upload_submitted:
                if uploaded_file and selected_record:
                    # 提取选中的记录 ID
                    selected_id = selected_record.split(" - ")[0]

                    # 定义文件路径
                    file_extension = os.path.splitext(uploaded_file.name)[1]
                    file_name = f"{selected_id}{file_extension}"
                    base_path = "test/"

                    try:
                        with open(base_path + file_name, "wb") as file:
                            file.write(uploaded_file.getbuffer())

                        update_record(
                            selected_id,
                            {"uploaded_time": datetime.now(timezone).isoformat()},
                        )
                        st.success("File uploaded and record updated successfully.")
                    except Exception as e:
                        st.error(f"An error occurred during file upload: {e}")

                    # 增加 data_version 以刷新缓存
                    st.session_state.data_version += 1

                    # Rerun to refresh data_editor
                    st.rerun()
                else:
                    st.error("Please select a record and upload a valid file.")
