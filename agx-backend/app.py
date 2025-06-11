from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from agx.core import agx_main 
from fastapi.middleware.cors import CORSMiddleware
# Slowapi for rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from redis import Redis

app = FastAPI()

# Allows requests from frontend on different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.97:3000"],  # Or "*" to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plan downloading
class Script(BaseModel):
    prompt: str

# Rate limiting
limiter = Limiter(key_func=get_remote_address,
                  storage_uri="redis://localhost:6379")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/", response_class=FileResponse)
@limiter.limit("5/day") # Set limits here
async def generate_script(script: Script, request: Request):
    code = agx_main(script.prompt)
    if not code:
        raise HTTPException(status_code=500, detail="Plan generation failed.")
    return code