import uvicorn
from service2.src2.config import settings
from service2.src2.application import get_app

app = get_app()

if __name__ == "__main__":
    uvicorn.run(
        "service2.src2.main:app",
        host=settings.service2_host,
        port=settings.service2_port,
        reload=True
    )