import uvicorn
from app.config import Config

if __name__ == "__main__":
    config = Config()
    uvicorn.run(
        "app.main:app",  # This should match the import path to your FastAPI app
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        workers=config.server.workers
    )