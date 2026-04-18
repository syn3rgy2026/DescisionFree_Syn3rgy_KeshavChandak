from tools.file_tool import (
    write_file, 
    create_excel_file, 
    create_word_document
)

# Test 1: Standard File Creation
print("Testing writing text file...")
out_txt = write_file("dummy.txt", "Hello from Synergy Agent!")
print(f"Created: {out_txt}")

# Test 2: Word Document Creation
print("\nTesting creating a Word document...")
out_word = create_word_document(
    filename="report.docx", 
    title="Synergy Agent Execution Report", 
    paragraphs=["This is an automated file operations test.", "It works perfectly!"]
)
print(f"Created Word Document: {out_word}")

# Test 3: Excel Creation
print("\nTesting creating an Excel file...")
out_xl = create_excel_file(
    filename="syn3rgy_data.xlsx", 
    headers=["ID", "Task Name", "Status"], 
    rows=[
        [1, "Initialize Agent", "Success"],
        [2, "System Operations", "Success"]
    ]
)
print(f"Created Excel File: {out_xl}")

print("\nAll tasks passed!")
