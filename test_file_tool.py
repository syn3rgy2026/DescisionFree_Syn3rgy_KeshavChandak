from tools.file_tool import FileTool

# Initialize the new FileTool
tool = FileTool()

# Test 1. Create a file
tool.create_file("test_workspace.txt")
print("1. File created.")

# Test 2. Write and Read
tool.write_file("test_workspace.txt", "Hello Synergy Agent, writing works!")
content = tool.read_file("test_workspace.txt")
print(f"2. File Content: {content}")

# Test 3. Rename and grab metadata
tool.rename_file("test_workspace.txt", "test_workspace_renamed.txt")
size = tool.get_file_size("test_workspace_renamed.txt")
print(f"3. Renamed file size: {size} bytes")

# Test 4. File Cleanup
tool.delete_file("test_workspace_renamed.txt")
print("4. File deleted.")

print("\n--- Auditing & Tool History Log ---")
for log in tool.get_history():
    print(log)
