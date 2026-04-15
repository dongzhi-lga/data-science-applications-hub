from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.routers.data_io import router as core_data_io_router
from app.modules.binary_feature_ae.routers.binary_feature import (
    router as binary_feature_router,
)
from app.modules.mortality_ae.routers.ae import router as ae_router
from app.modules.mortality_ae.routers.dataset_configs import (
    router as dataset_configs_router,
)
from app.routers.datasets import router as datasets_router
from app.routers.health import router as health_router
from app.routers.monitor import router as monitor_router
from app.service.storage import bootstrap_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_storage()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Data Science Applications Hub", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for local development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(core_data_io_router)
    app.include_router(datasets_router)
    app.include_router(dataset_configs_router)
    app.include_router(ae_router)
    app.include_router(binary_feature_router)
    app.include_router(monitor_router)
    return app


app = create_app()
