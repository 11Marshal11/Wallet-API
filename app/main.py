from fastapi import FastAPI

from app.routers import wallets


def create_app() -> FastAPI:
    app = FastAPI(title="Wallet API", version="1.0.0")
    app.include_router(wallets.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
