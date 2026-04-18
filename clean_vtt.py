
import sys

vtt_path = 'output/transcript.en.vtt'
txt_path = 'output/transcript.txt'

try:
    with open(vtt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    text_lines = []
    for line in lines:
        if "WEBVTT" in line or "-->" in line or not line.strip():
            continue
        clean_line = line.strip()
        if clean_line:
            text_lines.append(clean_line)

    full_text = []
    for line in text_lines:
        if not full_text or line != full_text[-1]:
            full_text.append(line)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(" ".join(full_text))
    print("Cleaning Success")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
