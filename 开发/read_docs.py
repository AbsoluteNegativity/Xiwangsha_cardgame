import docx
import os
import sys

# 设置控制台编码为UTF-8
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

def read_docx(file_path):
    """读取.docx文件并返回文本内容"""
    try:
        doc = docx.Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        return '\n'.join(text)
    except Exception as e:
        return f"读取文件时出错: {e}"

def main():
    base_path = r"D:\Xiwangsha\希望杀"
    
    # 读取主要文档
    files_to_read = [
        os.path.join(base_path, "Readme_Chinese.docx"),
        os.path.join(base_path, "卡牌说明.docx"),
        os.path.join(base_path, "角色", "角色文档.docx")
    ]
    
    for file_path in files_to_read:
        if os.path.exists(file_path):
            print(f"\n{'='*50}")
            print(f"文件: {os.path.basename(file_path)}")
            print(f"{'='*50}")
            content = read_docx(file_path)
            print(content)
            print(f"\n{'='*50}\n")
        else:
            print(f"文件不存在: {file_path}")

if __name__ == "__main__":
    main()
