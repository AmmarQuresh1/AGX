from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agx.core import agx_main # type: ignore Run from documents folder then it'll work

app = FastAPI()

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