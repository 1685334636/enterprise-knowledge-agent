"""仅在用户指定时读取本地单行密钥；不复制、打印或落盘密钥。"""
from pathlib import Path

from .backends import BackendError


def read_api_key_file(path):
    try:
        path = Path(path)
        if path.stat().st_size>8192:
            raise BackendError("密钥文件过大；应只包含单行密钥。")
        value = path.read_text(encoding="utf-8-sig").strip()
    except (OSError,UnicodeError):
        raise BackendError("无法读取本地密钥文件；未回显文件内容。") from None
    if not value or any(c.isspace() for c in value) or len(value)>4096:
        raise BackendError("密钥文件应只包含一个非空、无空白的密钥。")
    return value
