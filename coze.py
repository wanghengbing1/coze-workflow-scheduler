"""
This example describes how to use the workflow interface to chat.
"""

import os
import traceback
# Our official coze sdk for Python [cozepy](https://github.com/coze-dev/coze-py)
from cozepy import COZE_CN_BASE_URL

print("开始运行 Coze 工作流示例...")

try:
    # Get an access_token through personal access token or oauth.
    coze_api_token = 'sat_OqFBJARUwgHC2wsSwp2c0UVvectsbvQVSrJutIGwjMTNUEmVr7ZSxPZqBwPdKPrt'
    print(f"使用 API Token: {coze_api_token[:10]}...")
    
    # The default access is api.coze.com, but if you need to access api.coze.cn,
    # please use base_url to configure the api endpoint to access
    coze_api_base = COZE_CN_BASE_URL
    print(f"API 基础地址: {coze_api_base}")

    from cozepy import Coze, TokenAuth, Message, ChatStatus, MessageContentType  # noqa

    print("正在初始化 Coze 客户端...")
    # Init the Coze client through the access_token.
    coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)
    print("Coze 客户端初始化成功")

    # Create a workflow instance in Coze, copy the last number from the web link as the workflow's ID.
    workflow_id = '7569877408963231763'
    print(f"工作流 ID: {workflow_id}")

    print("正在创建工作流运行...")
    # Call the coze.workflows.runs.create method to create a workflow run. The create method
    # is a non-streaming chat and will return a WorkflowRunResult class.
    workflow = coze.workflows.runs.create(
        workflow_id=workflow_id,
    )
    
    print("工作流创建成功!")
    print("workflow.data:", workflow.data)
    print("工作流运行完成!")

except Exception as e:
    print(f"发生错误: {e}")
    print("错误详情:")
    traceback.print_exc()