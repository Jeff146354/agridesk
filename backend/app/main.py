from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.controllers import auth_controller, surat_controller, signature_controller, verification_controller, notification_controller
from app.database import SessionLocal
from app.utils.template_seed import seed_default_internal_templates
from app.domain.exceptions import (
    AgrideskError,
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    UnauthorizedError,
    ValidationError,
)

app = FastAPI(
    title="Agridesk API",
    description="Academic Letter Workflow System",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    # Allow the public domain (via Nginx Proxy Manager) and local dev origins.
    # Add your public frontend domain here if it differs from the backend domain.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://mtf.idenx.id",
        "https://drive.hq.idenx.id",
        # Allow same-origin requests coming through nginx proxy manager
        # (browser sends Origin matching the public domain)
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Structured error handlers for domain exceptions
# ------------------------------------------------------------------

_HTTP_STATUS_MAP = {
    "ENTITY_NOT_FOUND": 404,
    "INVALID_STATE_TRANSITION": 409,
    "UNAUTHORIZED": 403,
    "VALIDATION_ERROR": 400,
    "DUPLICATE_ENTITY": 409,
    "INTERNAL_ERROR": 500,
}


@app.exception_handler(AgrideskError)
async def agridesk_error_handler(request, exc: AgrideskError):
    status_code = _HTTP_STATUS_MAP.get(exc.code, 400)
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


# Register routers
app.include_router(auth_controller.router)
app.include_router(surat_controller.router)
app.include_router(signature_controller.router)
app.include_router(verification_controller.router)
app.include_router(notification_controller.router)


@app.on_event("startup")
def seed_letter_templates() -> None:
    db = SessionLocal()
    try:
        seed_default_internal_templates(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Agridesk API is running"}
