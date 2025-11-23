
import asyncio
import logging
from pathlib import Path
from gitvisioncli.core.chat_engine import ChatEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("--- VERIFICATION START ---")
    base_dir = Path.cwd()
    
    engine = ChatEngine(
        base_dir=base_dir,
        api_key="test-key",
        model="gpt-4o-mini",
        dry_run=False
    )
    
    # Test OverwriteFile with content
    action = {
        "type": "RewriteEntireFile",  # Canonical name for OverwriteFile
        "params": {
            "path": "verify_test.txt",
            "content": "Verification Successful!"
        }
    }
    
    print(f"Running action: {action}")
    result = engine.executor.run_action(action, context=None)
    
    print(f"Result status: {result.status}")
    print(f"Result message: {result.message}")
    
    file_path = base_dir / "verify_test.txt"
    if file_path.exists():
        content = file_path.read_text()
        print(f"File content: '{content}'")
        if content == "Verification Successful!":
            print("SUCCESS: Content written correctly")
        else:
            print("FAILURE: Content mismatch")
        file_path.unlink()
    else:
        print("FAILURE: File NOT created")

if __name__ == "__main__":
    asyncio.run(main())
