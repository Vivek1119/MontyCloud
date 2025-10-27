import uvicorn
from fastapi import FastAPI, status
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from services.logger import logger
from api.routes import upload, image

@asynccontextmanager
async  def lifespan(app: FastAPI):
    logger.info("app_start", action="initializing app")
    yield


app = FastAPI(title="Monte Cloudgram",
              description="This service provides scalable image upload and storage functionality for an Instagram-like application. "
                          "It allows multiple users to upload images concurrently, stores image files securely in the Cloud, and "
                          "persists associated metadata in a NoSQL database. The service is designed for high availability, scalability, "
                          "and efficient media management.",
              lifespan=lifespan)


@app.get("/", tags=["System"])
async def health_check():
    return JSONResponse(
        content={"message": "system is healthy"},
        status_code=status.HTTP_200_OK
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router ,prefix="/api/v1")
app.include_router(image.router ,prefix="/api/v1")

if __name__ == '__main__':
    uvicorn.run("app:app", port=8001, host="localhost", reload=True)