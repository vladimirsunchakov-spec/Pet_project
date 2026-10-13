import uvicorn
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main() -> None:
    uvicorn.run('src.application:get_app', host='localhost', port=8000, reload=True, factory=True)

if __name__ == '__main__':
    asyncio.run(main())
