import os
import streamlit as st
from langgraph.pregel.remote import RemoteGraph

url = st.secrets["langgraph"]["url"]
api_key = st.secrets["langgraph"]["api_key"]
graph_name = "esg_search_agent"

remote_graph = RemoteGraph(graph_name, url=url, api_key=api_key)

import asyncio


async def main():
    result = await remote_graph.ainvoke(
        {"messages": [{"role": "user", "content": "3M India Ltd. 2023"}]}
    )
    print(result)


asyncio.run(main())
