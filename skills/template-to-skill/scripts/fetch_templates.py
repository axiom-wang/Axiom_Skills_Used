"""
获取指定 chat_id 的模板对话历史。

用法：
    python scripts/fetch_templates.py <chat_id> [version]

示例：
    python scripts/fetch_templates.py abc123
    python scripts/fetch_templates.py abc123 v2
"""

import requests
import json
import os
import sys

# 配置
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3NiIsImVtYWlsIjoieHV5b3V3YW5AZnV6aGkuYWkiLCJ2ZXIiOjEsImV4cCI6MTc4Mzk5NjM3M30.g_f6MkrV4PmeY80OFHXrkTfac3_Y1kTF60TAINTw9_U"
DEFAULT_BASE_DIR = os.path.expanduser("~/Downloads/template-to-skill")

ATOMS_BASE = "https://atoms.dev/api/v1/public"
LOGS_BASE = "http://test-tool.deepwisdomai.com/api/v1/chats"


def fetch_template_detail(chat_id):
    """获取单个模板详情（含 version 信息）"""
    url = f"{ATOMS_BASE}/chats"
    params = {
        "chat_ids": chat_id,
        "page_num": 1,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    data_list = data["data"]["data_list"]
    if not data_list:
        return None
    return data_list[0]


def fetch_chat_logs(chat_id, version):
    """获取对话历史"""
    url = f"{LOGS_BASE}/{chat_id}/logs"
    params = {
        "env": "prod",
        "mgxenv": 1,
        "version": version,
    }
    headers = {"Authorization": f"Bearer {TOKEN}"}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/fetch_templates.py <chat_id> [version]")
        sys.exit(1)

    chat_id = sys.argv[1]
    version_override = sys.argv[2] if len(sys.argv) > 2 else None

    output_dir = os.path.join(DEFAULT_BASE_DIR, chat_id)

    os.makedirs(output_dir, exist_ok=True)

    # 获取模板详情确定 version
    if version_override:
        version = version_override
        title = chat_id
    else:
        print(f"📋 获取模板详情 ({chat_id})...")
        detail = fetch_template_detail(chat_id)
        if detail:
            title = detail.get("title", chat_id)
            version_info = detail.get("version") or {}
            version = version_info.get("version", "v1")
        else:
            title = chat_id
            version = "v1"

    print(f"💬 获取对话历史: {title} ({chat_id}, {version})")

    logs = fetch_chat_logs(chat_id, version)

    filename = f"conversation.json"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"✅ 保存到 {filepath}")


if __name__ == "__main__":
    main()
