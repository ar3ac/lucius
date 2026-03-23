from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import subprocess, json
import asyncio


app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates = Jinja2Templates(directory="templates")


def load_commands():
    try:
        with open("commands.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_commands(commands):
    with open("commands.json", "w") as f:
        json.dump(commands, f, indent=4)


@app.get("/")
def index(request: Request):
    commands = load_commands()  # Load commands from JSON file
    return templates.TemplateResponse(
        request=request, name="index.html", context={"commands": commands}
    )


@app.post("/run")
def run_command(request: Request, command: str = Form(...)):
    cmd_list = command.split()
    print(f"Running command: {cmd_list}")
    try:
        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        output = result.stdout
    except subprocess.CalledProcessError as e:
        output = e.stdout
        error = e.stderr
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "output": output,
            "error": error if "error" in locals() else None,
            "commands": load_commands(),
        },
    )
