from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
from dotenv import load_dotenv
import subprocess, json, re, os

load_dotenv()
LUCIUS_PIN = os.getenv("LUCIUS_PIN", "1234")

app = FastAPI()

@app.exception_handler(401)
async def custom_401_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/login", status_code=303)

def check_auth(request: Request):
    if request.cookies.get("lucius_auth") != "ok":
        raise HTTPException(status_code=401)
app.mount("/static", StaticFiles(directory="static"), name="static")
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


@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
def login_post(request: Request, response: Response, pin: str = Form(...)):
    if pin == LUCIUS_PIN:
        redirect = RedirectResponse(url="/", status_code=303)
        redirect.set_cookie(key="lucius_auth", value="ok", httponly=True, max_age=86400*30) # Expires in 30 days
        return redirect
    return templates.TemplateResponse(request=request, name="login.html", context={"error": "Incorrect PIN"})

@app.get("/logout")
def logout():
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("lucius_auth")
    return redirect


@app.get("/")
def index(request: Request, _ = Depends(check_auth)):
    return templates.TemplateResponse(request=request, name="index.html", context={"commands": load_commands(), "output": None, "error": None, "hostname": socket.gethostname()})


@app.get("/manage")
def manage(request: Request, _ = Depends(check_auth)):
    commands = load_commands()
    return templates.TemplateResponse(
        request=request, name="manage.html", context={"commands": commands, "hostname": socket.gethostname()}
    )


@app.post("/run")
def run_command(request: Request, command: str = Form(...), _ = Depends(check_auth)):
    commands_dict = load_commands()
    
    # 1. Security: check if the key exists in commands.json
    if command not in commands_dict:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "output": None,
                "error": "Security Error: Unauthorized command.",
                "commands": commands_dict,
                "hostname": socket.gethostname()
            },
        )
        
    # 2. Get the actual command string and split it
    actual_cmd_string = commands_dict[command]
    cmd_list = actual_cmd_string.split()
    print(f"Running command: {cmd_list}")
    
    output = None
    error = None
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
    except subprocess.TimeoutExpired:
        error = "Error: Command timed out after 60 seconds. (Is it waiting for a sudo password?)"
    except FileNotFoundError:
        # Handle the case where the executable (e.g., 'uptime') is not found in the system
        error = f"Error: Executable not found for '{cmd_list[0]}'"
        
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "output": output,
            "error": error,
            "commands": commands_dict,
            "hostname": socket.gethostname()
        },
    )

@app.post("/add")
def add_command(request: Request, name: str = Form(...), cmd: str = Form(...), _ = Depends(check_auth)):
    name = name.strip()
    cmd = cmd.strip()
    
    # 1. Validate name: no spaces, only alphanumerics and underscores
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={
                "commands": load_commands(),
                "error": "Error: Name can only contain letters, numbers, and underscores.",
                "hostname": socket.gethostname()
            }
        )
        
    commands = load_commands()
    
    # 2. Validate name: must not already exist
    if name in commands:
        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={
                "commands": commands,
                "error": f"Error: A command named '{name}' already exists.",
                "hostname": socket.gethostname()
            }
        )
        
    # Save new command
    commands[name] = cmd
    save_commands(commands)
    
    # GET Redirect to /manage to reload the page
    return RedirectResponse(url="/manage", status_code=303)


@app.post("/delete")
def delete_command(request: Request, name: str = Form(...), _ = Depends(check_auth)):
    commands = load_commands()
    if name in commands:
        del commands[name]
        save_commands(commands)
        
    return RedirectResponse(url="/manage", status_code=303)


@app.post("/edit")
def edit_command(request: Request, name: str = Form(...), cmd: str = Form(...), old_name: str = Form(...), _ = Depends(check_auth)):
    name = name.strip()
    cmd = cmd.strip()
    
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return templates.TemplateResponse(
            request=request, name="manage.html", context={
                "commands": load_commands(), "error": "Error: Name can only contain letters, numbers, and underscores.", "hostname": socket.gethostname()
            }
        )
        
    commands = load_commands()
    
    if old_name not in commands:
         return RedirectResponse(url="/manage", status_code=303)
         
    if name != old_name and name in commands:
        return templates.TemplateResponse(
            request=request, name="manage.html", context={
                "commands": commands, "error": f"Error: A command named '{name}' already exists.", "hostname": socket.gethostname()
            }
        )
        
    del commands[old_name]
    commands[name] = cmd
    save_commands(commands)
    
    return RedirectResponse(url="/manage", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
