def test_addition():
    """Test basic addition"""
    assert 1 + 1 == 2, "Addition failed!"
    print("✓ Addition test passed")

def test_string_operations():
    """Test string operations"""
    assert "hello" + " " + "world" == "hello world", "String concatenation failed!"
    print("✓ String operations test passed")

def test_list_operations():
    """Test list operations"""
    my_list = [1, 2, 3]
    assert len(my_list) == 3, "List length failed!"
    assert sum(my_list) == 6, "List sum failed!"
    print("✓ List operations test passed")

if __name__ == "__main__":
    print("Running tests...")
    print("-" * 40)
    test_addition()
    test_string_operations()
    test_list_operations()
    print("-" * 40)
    print("All tests passed! ✓")