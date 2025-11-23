
import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gitvisioncli")

from gitvisioncli.core.chat_engine import ChatEngine
from gitvisioncli.core.executor import AIActionExecutor
from gitvisioncli.core.supervisor import ActionContext

async def main():
    print("--- DEBUG START ---")
    base_dir = Path.cwd()
    
    # Initialize Engine explicitly with dry_run=False
    print(f"Initializing ChatEngine with dry_run=False")
    engine = ChatEngine(
        base_dir=base_dir,
        api_key="test-key",
        model="gpt-4o-mini",
        dry_run=False
    )
    
    print(f"Engine initialized. Engine.dry_run={engine.executor.dry_run}")
    
    # Create a test action
    action = {
        "type": "CreateFile",
        "params": {
            "path": "debug_test.txt",
            "content": "debug content"
        }
    }
    
    print(f"Running action: {action}")
    
    # Run action
    # We access executor directly to test run_action
    result = engine.executor.run_action(action, context=None)
    
    print(f"Result status: {result.status}")
    print(f"Result message: {result.message}")
    
    if (base_dir / "debug_test.txt").exists():
        print("SUCCESS: File created on disk")
        (base_dir / "debug_test.txt").unlink()
    else:
        print("FAILURE: File NOT created on disk")

if __name__ == "__main__":
    asyncio.run(main())
