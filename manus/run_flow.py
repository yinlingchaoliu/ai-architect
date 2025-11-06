# run_flow.py
import asyncio
import sys
from manus.main import MultiAgentSystem

async def run_flow(task: str):
    """运行工作流"""
    system = MultiAgentSystem()
    await system.initialize()
    result = await system.run(task)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = asyncio.run(run_flow(task))
        print("Execution completed:")
        print(f"Task: {task}")
        print(f"Result: {result}")
    else:
        print("Please provide a task as argument")
        print("Usage: python run_flow.py 'your task here'")