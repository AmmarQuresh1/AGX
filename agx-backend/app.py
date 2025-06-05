from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agx.core import agx_main 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Or "*" to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Script(BaseModel):
    prompt: str

@app.post("/", response_class=FileResponse)
async def generate_script(script: Script):
    plan = agx_main(script.prompt)
    if not plan:
        raise HTTPException(status_code=500, detail="Plan generation failed.")
    filename = "plan.py"
    with open(filename, "w") as f:
        f.write(plan)
    return FileResponse(filename)