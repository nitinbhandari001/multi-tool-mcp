import os
import stat
from pathlib import Path
from datetime import datetime, timezone
from ..exceptions import PathTraversalError
from ..models import FileEntry


class FilesystemService:
    def __init__(
        self,
        workspace_root: str,
        max_file_size: int,
        allowed_extensions: set[str],
    ):
        self._root = Path(workspace_root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._max_size = max_file_size
        self._allowed_exts = allowed_extensions

    def _safe_path(self, relative: str) -> Path:
        """Resolve path and verify it stays within workspace root."""
        path = (self._root / relative).resolve()
        try:
            path.relative_to(self._root)
        except ValueError:
            raise PathTraversalError(f"Path '{relative}' escapes workspace root")
        return path

    def _validate_write(self, path: Path, content: str) -> None:
        ext = path.suffix.lower()
        if self._allowed_exts and ext not in self._allowed_exts:
            raise ValueError(f"Extension '{ext}' not allowed")
        if len(content.encode("utf-8")) > self._max_size:
            raise ValueError(f"Content exceeds max size of {self._max_size} bytes")

    async def read_file(self, relative: str) -> str:
        path = self._safe_path(relative)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {relative}")
        return path.read_text(encoding="utf-8")

    async def write_file(self, relative: str, content: str) -> str:
        path = self._safe_path(relative)
        self._validate_write(path, content)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} characters to {relative}"

    async def list_directory(self, relative: str = ".") -> list[FileEntry]:
        path = self._safe_path(relative)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {relative}")
        entries = []
        for item in sorted(path.iterdir()):
            item_stat = item.stat()
            entries.append(FileEntry(
                name=item.name,
                path=str(item.relative_to(self._root)),
                is_dir=item.is_dir(),
                size=None if item.is_dir() else item_stat.st_size,
                modified=datetime.fromtimestamp(item_stat.st_mtime, tz=timezone.utc).isoformat(),
            ))
        return entries

    async def file_info(self, relative: str) -> FileEntry:
        path = self._safe_path(relative)
        if not path.exists():
            raise FileNotFoundError(f"Not found: {relative}")
        s = path.stat()
        return FileEntry(
            name=path.name,
            path=str(path.relative_to(self._root)),
            is_dir=path.is_dir(),
            size=None if path.is_dir() else s.st_size,
            modified=datetime.fromtimestamp(s.st_mtime, tz=timezone.utc).isoformat(),
        )

    async def delete_file(self, relative: str) -> str:
        path = self._safe_path(relative)
        if not path.exists():
            raise FileNotFoundError(f"Not found: {relative}")
        if path.is_dir():
            raise IsADirectoryError(f"Use a directory removal tool, not delete_file: {relative}")
        path.unlink()
        return f"Deleted: {relative}"
