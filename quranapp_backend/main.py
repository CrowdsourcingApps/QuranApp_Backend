from fastapi import FastAPI
from fastapi.responses import JSONResponse

import src.startup as startup
from src.controllers import settings, users, recordings, tokens

app = FastAPI()


@app.exception_handler(Exception)
async def validation_exception_handler(request, err):
    base_error_message = f'Failed to execute: {request.method}: {request.url}'
    return JSONResponse(status_code=500, content={'message': f'{base_error_message}. Detail: {err}'})


# Include routers in the app
app.include_router(users)
app.include_router(recordings)
app.include_router(settings)
app.include_router(tokens)

startup.apply_migrations()
