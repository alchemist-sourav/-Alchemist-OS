import pytest
import os
import shutil
import tempfile
from tools.file_agent import list_directory, search_files, move_file, delete_file, read_metadata
from tools.registry import registry

@pytest.fixture
def temp_env():
    # Create a temporary directory structure for testing
    test_dir = tempfile.mkdtemp()
    
    # Create some files
    file1 = os.path.join(test_dir, "test1.txt")
    with open(file1, "w") as f:
        f.write("hello")
        
    sub_dir = os.path.join(test_dir, "subdir")
    os.mkdir(sub_dir)
    
    file2 = os.path.join(sub_dir, "searchme.txt")
    with open(file2, "w") as f:
        f.write("world")
        
    yield test_dir
    
    # Cleanup
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_list_directory(temp_env):
    result = list_directory(temp_env)
    assert "test1.txt" in result
    assert "subdir" in result
    
    bad_result = list_directory("non_existent_dir_123")
    assert "Error:" in bad_result

def test_search_files(temp_env):
    result = search_files("searchme", temp_env)
    assert "searchme.txt" in result
    assert "Found 1 files" in result
    
    no_result = search_files("nonexistent_file_name", temp_env)
    assert "No files matching" in no_result

def test_move_file(temp_env):
    src = os.path.join(temp_env, "test1.txt")
    dest = os.path.join(temp_env, "subdir", "test1_moved.txt")
    
    result = move_file(src, dest)
    assert "Successfully moved" in result
    assert not os.path.exists(src)
    assert os.path.exists(dest)
    
    bad_result = move_file("nonexistent.txt", dest)
    assert "Error:" in bad_result

def test_delete_file(temp_env):
    file_to_delete = os.path.join(temp_env, "test1.txt")
    result = delete_file(file_to_delete)
    assert "Successfully deleted file" in result
    assert not os.path.exists(file_to_delete)
    
    dir_to_delete = os.path.join(temp_env, "subdir")
    result_dir = delete_file(dir_to_delete)
    assert "Successfully deleted directory" in result_dir
    assert not os.path.exists(dir_to_delete)

def test_read_metadata(temp_env):
    file_path = os.path.join(temp_env, "test1.txt")
    result = read_metadata(file_path)
    assert "Metadata for" in result
    assert "Type: File" in result
    assert "Size: 5" in result # "hello" is 5 bytes
    
    dir_path = os.path.join(temp_env, "subdir")
    result_dir = read_metadata(dir_path)
    assert "Type: Directory" in result_dir

def test_registry_integration():
    import tools.file_agent # Ensure it's imported
    assert registry.get_tool("list_directory") is not None
    assert registry.get_tool("search_files") is not None
    assert registry.get_tool("move_file") is not None
    assert registry.get_tool("delete_file") is not None
    assert registry.get_tool("read_metadata") is not None
