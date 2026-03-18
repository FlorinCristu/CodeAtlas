import os
from pathlib import Path
from mcp_code_constellation.server import index_target_repo, search_flow, get_function_constellation

def setup_mock_repo():
    mock_dir = Path("mock_repo")
    mock_dir.mkdir(exist_ok=True)
    
    (mock_dir / "auth.py").write_text("""
def hash_password(pw):
    return pw + "hash"
    
def query_db(user):
    return user
    
def login(user, pw):
    print("starting login")
    u = query_db(user)
    h = hash_password(pw)
    return True
""")
    return str(mock_dir.resolve())

def test():
    repo_path = setup_mock_repo()
    
    # 1. Test indexing
    print("Testing index...")
    res = index_target_repo(repo_path)
    print(res)
    assert "Successfully indexed 3" in res, "Should index 3 functions"
    
    # 2. Test Constellation
    print("\nTesting Get Constellation for 'hash_password'...")
    res_const = get_function_constellation("hash_password", depth=1)
    print(res_const)
    assert "login" in res_const, "Upstream caller 'login' should be found"
    
    # 3. Test Flow
    print("\nTesting Semantic Search Flow for 'authentication login flow'...")
    res_flow = search_flow("authentication login flow", depth=2)
    print(res_flow)
    assert "login" in res_flow, "Should find login as entry point"
    assert "hash_password" in res_flow, "Should include downstream node hash_password"
    assert "query_db" in res_flow, "Should include downstream node query_db"
    
    print("\n✅ All tests passed!")
    
if __name__ == "__main__":
    test()
