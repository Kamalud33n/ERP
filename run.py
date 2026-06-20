import uvicorn
import os

if __name__ == "__main__":
    is_dev = os.getenv("ENV", "production") == "development"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("API_PORT", 8000)),
        reload=is_dev,
        workers=1 if is_dev else 4,
        log_level="info"
    )