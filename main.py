import uvicorn
from app.config import Config

if __name__ == "__main__":
    config = Config()
    uvicorn.run(
        app="app.main:app",
        host=config.ip_address,
        port=config.port,
        reload=True
    )
