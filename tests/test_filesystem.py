import pytest
from pathlib import Path
from multi_tool_mcp.services.filesystem import FilesystemService
from multi_tool_mcp.exceptions import PathTraversalError

ALLOWED_EXTS = {".txt", ".md", ".csv", ".json"}


def make_fs(tmp_path):
    return FilesystemService(str(tmp_path), max_file_size=1024, allowed_extensions=ALLOWED_EXTS)


async def test_read_file_in_sandbox(tmp_path):
    """Can read file within workspace."""
    (tmp_path / "hello.txt").write_text("Hello world")
    fs = make_fs(tmp_path)
    content = await fs.read_file("hello.txt")
    assert content == "Hello world"


async def test_path_traversal_blocked(tmp_path):
    """Path traversal outside workspace raises PathTraversalError."""
    fs = make_fs(tmp_path)
    with pytest.raises(PathTraversalError):
        await fs.read_file("../../etc/passwd")


async def test_write_creates_file(tmp_path):
    """write_file creates the file with content."""
    fs = make_fs(tmp_path)
    await fs.write_file("output.txt", "test content")
    assert (tmp_path / "output.txt").read_text() == "test content"


async def test_write_creates_parent_dirs(tmp_path):
    """write_file creates parent directories."""
    fs = make_fs(tmp_path)
    await fs.write_file("subdir/nested/file.txt", "nested")
    assert (tmp_path / "subdir" / "nested" / "file.txt").exists()


async def test_size_limit_enforced(tmp_path):
    """write_file rejects content exceeding max_file_size."""
    fs = make_fs(tmp_path)  # max 1024 bytes
    big_content = "x" * 2000
    with pytest.raises(ValueError, match="max size"):
        await fs.write_file("big.txt", big_content)


async def test_blocked_extension_rejected(tmp_path):
    """write_file rejects files with disallowed extensions."""
    fs = make_fs(tmp_path)
    with pytest.raises(ValueError, match="Extension"):
        await fs.write_file("script.py", "print('hello')")


async def test_list_directory(tmp_path):
    """list_directory returns FileEntry list."""
    (tmp_path / "a.txt").write_text("A")
    (tmp_path / "b.md").write_text("B")
    fs = make_fs(tmp_path)
    entries = await fs.list_directory(".")
    names = [e.name for e in entries]
    assert "a.txt" in names
    assert "b.md" in names


async def test_delete_file(tmp_path):
    """delete_file removes the file."""
    f = tmp_path / "to_delete.txt"
    f.write_text("bye")
    fs = make_fs(tmp_path)
    result = await fs.delete_file("to_delete.txt")
    assert not f.exists()
    assert "Deleted" in result
