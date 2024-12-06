import streamlit as st
import pandas as pd
from supabase import Client, create_client

st.set_page_config(
    page_title="Journal Papers",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化 Supabase 客户端
supabase: Client = create_client(st.secrets.supabase.url, st.secrets.supabase.key)

@st.cache_data(show_spinner=False, ttl=600)
def get_total_count():
    try:
        # 使用 count='exact' 来获取总行数
        count_response = supabase.table("esg_meta").select("*", count='exact').execute()
        return count_response.count
    except Exception as e:
        st.error(f"获取总行数时出错: {e}")
        return 0

@st.cache_data(show_spinner=False, ttl=600)
def get_columns():
    try:
        # 仅获取一条记录来提取列名
        response = supabase.table("esg_meta").select("*").limit(1).execute()
        if response.data:
            return list(response.data[0].keys())
        else:
            return []
    except Exception as e:
        st.error(f"获取列名时出错: {e}")
        return []

@st.cache_data(show_spinner=False)
def fetch_data(page_number: int, page_size: int, sort_field: str = None, sort_order: str = "asc"):
    try:
        query = supabase.table("esg_meta").select("*")
        
        if sort_field:
            query = query.order(sort_field, desc=(sort_order == "desc"))
        
        start = (page_number - 1) * page_size
        
        response = query.limit(page_size).offset(start).execute()
        dataset = pd.DataFrame(response.data)
        return dataset
    except Exception as e:
        st.error(f"获取数据时出错: {e}")
        return pd.DataFrame()

# 获取总行数
total_count = get_total_count()

# 获取列名
columns = get_columns()

# 顶部菜单：排序选项
top_menu = st.columns(3)
with top_menu[0]:
    sort = st.radio("Sort Data", options=["Yes", "No"], horizontal=True, index=1)
if sort == "Yes" and columns:
    with top_menu[1]:
        sort_field = st.selectbox("Sort By", options=columns)
    with top_menu[2]:
        sort_direction = st.radio("Direction", options=["⬆️ Ascending", "⬇️ Descending"], horizontal=True)
        sort_order = "asc" if sort_direction == "⬆️ Ascending" else "desc"
else:
    sort_field = None
    sort_order = "asc"

# 底部菜单：分页控制
bottom_menu = st.columns((4, 1, 1))
with bottom_menu[2]:
    batch_size = st.selectbox("Page Size", options=[25, 50, 100], index=0)
with bottom_menu[1]:
    total_pages = max(1, (total_count + batch_size - 1) // batch_size)
    current_page = st.number_input(
        "Page", min_value=1, max_value=total_pages, step=1, value=1
    )
with bottom_menu[0]:
    st.markdown(f"Page **{current_page}** of **{total_pages}** ")

# 获取当前页的数据
dataset = fetch_data(current_page, batch_size, sort_field, sort_order)

# 显示数据
st.data_editor(
    data=dataset,
    use_container_width=True,
    num_rows="dynamic",
    height=1000
)
