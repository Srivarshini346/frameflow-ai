import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from cli.run_test_pack import run_pack

if __name__ == "__main__":
    asyncio.run(run_pack())
