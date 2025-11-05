# 测试导入脚本
print("尝试导入BaseExpert...")
try:
    from graph_discussion.agents.experts.base_expert import BaseExpert
    print("成功导入BaseExpert!")
except Exception as e:
    print(f"导入失败: {type(e).__name__}: {str(e)}")
    import sys
    print(f"Python路径: {sys.path}")

print("\n检查文件是否存在...")
import os
file_path = "/Users/chentong/phoenix/project/ai-architect/graph_discussion/agents/experts/base_expert.py"
print(f"文件存在: {os.path.exists(file_path)}")
print(f"文件内容预览:")
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        print(f.read()[:200] + "...")