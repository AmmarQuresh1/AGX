from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
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
    allow_origins=["http://localhost:3000", 
                   "https://www.agx.run",
                   "https://vercel.com/ammars-projects-de451d5d/agx/Fj8ZgWqZ61x6XFs1BFyAJVq28rsA",
                   "agx-sandy.vercel.app",
                   "https://agx.run"],  # Or "*" to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plan downloading
class Script(BaseModel):
    prompt: str

# Rate limiting
limiter = Limiter(key_func=get_remote_address,
                  storage_uri="redis://:fa12cbe52d09461c98fd1e4a5e853304@fly-agx-backend-redis.upstash.io:6379") # redis://localhost:6379
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/", response_class=PlainTextResponse)
@limiter.limit("5/day") # Set limits here
async def generate_script(script: Script, request: Request):
    code = agx_main(script.prompt)
    if not code:
        raise HTTPException(status_code=500, detail="Plan generation failed.")
    return code