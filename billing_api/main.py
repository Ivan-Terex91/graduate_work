import logging

import uvicorn as uvicorn
from api.v1 import billing
from core import auth, config
from core.logger import LOGGING
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(
    title=config.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.on_event("startup")
async def startup():
    auth.auth_client = auth.AuthClient(base_url=config.AUTH_URL)


@app.on_event("shutdown")
async def shutdown():
    pass


app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,  # type: ignore
        log_config=LOGGING,
        log_level=logging.DEBUG,
        reload=True,
    )