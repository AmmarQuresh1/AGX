from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from AGX.main import main as agx_main # type: ignore Run from documents folder then it'll work

app = FastAPI()

class Script(BaseModel):
    prompt: str

@app.post("/", response_class=FileResponse)
async def generate_script(script: Script):
    plan = await agx_main(script.prompt)
    filename = "plan.py"
    with open(filename, "w") as f:
        f.write(plan)
    return FileResponse(filename)