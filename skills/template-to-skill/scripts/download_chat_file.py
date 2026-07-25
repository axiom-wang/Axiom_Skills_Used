#!/usr/bin/env python3
"""下载指定 chat_id 的 workspace 全部文件到本地。

Usage:
    python scripts/download_chat_file.py <chat_id> [output_dir]

示例:
    python scripts/download_chat_file.py abc-def-123
    python scripts/download_chat_file.py abc-def-123 ~/Downloads/template-to-skill/abc-def-123/source
"""

import os
import sys
from urllib.parse import urlparse, urlunparse

import requests

# 配置
BASE_URL = "http://test-tool.deepwisdomai.com"
EMAIL = "xuyouwan@fuzhi.ai"
PASSWORD = "X2y7W$0$"
# admin user_id（用于 admin API）
ADMIN_USER_ID = 76


def login(base_url: str) -> str:
    resp = requests.post(
        f"{base_url}/api/v1/user/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        print(f"登录失败: {data.get('message')}", file=sys.stderr)
        sys.exit(1)
    return data["data"]["token"]


def list_workspace_files(base_url: str, token: str, chat_id: str) -> list:
    """列出 workspace 中的所有文件（递归）"""
    resp = requests.get(
        f"{base_url}/api/v1/admin/chats/file/list",
        headers={"Authorization": token},
        params={"chat_id": chat_id, "user_id": ADMIN_USER_ID},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        print(f"列出文件失败: {data.get('message')}", file=sys.stderr)
        sys.exit(1)
    return data["data"]["files"]


def get_download_url(base_url: str, token: str, chat_id: str, path: str) -> str:
    resp = requests.get(
        f"{base_url}/api/v1/admin/chats/file/download-url",
        headers={"Authorization": token},
        params={"user_id": ADMIN_USER_ID, "chat_id": chat_id, "path": path},
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        return None
    return data["data"]["download_url"]


def download_file(base_url: str, url: str, output_path: str):
    """下载文件，替换 URL 中的内网域名"""
    parsed_base = urlparse(base_url)
    parsed_dl = urlparse(url)
    url = urlunparse(parsed_dl._replace(scheme=parsed_base.scheme, netloc=parsed_base.netloc))

    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


# 跳过的骨架/无关文件模式
SKIP_PATTERNS = [
    "node_modules/",
    ".git/",
    "__pycache__/",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    ".env",
]


def should_skip(path: str) -> bool:
    for pattern in SKIP_PATTERNS:
        if pattern in path:
            return True
    return False


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/download_chat_file.py <chat_id> [output_dir]")
        sys.exit(1)

    chat_id = sys.argv[1]
    default_output = os.path.expanduser(f"~/Downloads/template-to-skill/{chat_id}/source")
    output_dir = sys.argv[2] if len(sys.argv) > 2 else default_output

    print(f"🔐 登录...")
    token = login(BASE_URL)

    print(f"📂 列出 workspace 文件 ({chat_id})...")
    files = list_workspace_files(BASE_URL, token, chat_id)
    print(f"   共 {len(files)} 个文件")

    # 过滤
    to_download = [f for f in files if not should_skip(f)]
    print(f"   过滤后 {len(to_download)} 个文件需要下载")

    # 下载
    success = 0
    failed = 0
    for i, file_path in enumerate(to_download, 1):
        print(f"   [{i}/{len(to_download)}] {file_path}")
        try:
            url = get_download_url(BASE_URL, token, chat_id, file_path)
            if not url:
                print(f"      ⏭ 跳过（无下载链接）")
                continue
            output_path = os.path.join(output_dir, file_path)
            download_file(BASE_URL, url, output_path)
            success += 1
        except Exception as e:
            print(f"      ❌ 失败: {e}")
            failed += 1

    print(f"\n✅ 完成! 成功 {success}, 失败 {failed}, 保存到 {output_dir}")


if __name__ == "__main__":
    main()
