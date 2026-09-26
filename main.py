from fastapi import (
    FastAPI,
    Request,
    Form,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from dotenv import load_dotenv
import subprocess, json, re, os, shlex, asyncio
from datetime import datetime

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


@app.get("/sw.js")
def service_worker():
    return Response(
        content=open("static/sw.js", "r").read(), media_type="application/javascript"
    )


SETTINGS_FILE = "settings.json"


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"server_name": "Lucius"}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"server_name": "Lucius"}


def save_settings(settings_dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings_dict, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def get_server_name():
    return load_settings().get("server_name", "Lucius")


def load_commands():
    try:
        with open("commands.json", "r") as f:
            data = json.load(f)
            migrated = False
            for k, v in list(data.items()):
                if isinstance(v, str):
                    data[k] = {"cmd": v, "enabled": True}
                    migrated = True
            if migrated:
                save_commands(data)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_commands(commands):
    with open("commands.json", "w") as f:
        json.dump(commands, f, indent=4)


LOGS_FILE = "history.json"
MAX_LOGS = 50


def append_log(command_name, cmd_string, success, output):
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f:
                logs = json.load(f)
        except:
            pass

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "command": command_name,
        "script": cmd_string,
        "success": success,
        "output": (
            output[-1000:] if output else ""
        ),  # Keep last 1000 chars to avoid huge files
    }

    logs.insert(0, log_entry)
    logs = logs[:MAX_LOGS]

    try:
        with open(LOGS_FILE, "w") as f:
            json.dump(logs, f, indent=4)
    except:
        pass


@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/login")
def login_post(request: Request, response: Response, pin: str = Form(...)):
    if pin == LUCIUS_PIN:
        redirect = RedirectResponse(url="/", status_code=303)
        redirect.set_cookie(
            key="lucius_auth", value="ok", httponly=True, max_age=86400 * 30
        )  # Expires in 30 days
        return redirect
    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": "Incorrect PIN"}
    )


@app.get("/logout")
def logout():
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("lucius_auth")
    return redirect


@app.get("/")
def index(request: Request, _=Depends(check_auth)):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "commands": load_commands(),
            "output": None,
            "error": None,
            "server_name": get_server_name(),
        },
    )


@app.get("/logs")
def view_logs(request: Request, _=Depends(check_auth)):
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f:
                logs = json.load(f)
        except:
            pass
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"logs": logs, "server_name": get_server_name()},
    )


@app.post("/settings")
def update_settings(
    request: Request, server_name: str = Form(...), _=Depends(check_auth)
):
    try:
        settings = load_settings()
        settings["server_name"] = server_name.strip() or "Lucius"
        if not save_settings(settings):
            return templates.TemplateResponse(
                request=request,
                name="manage.html",
                context={
                    "commands": load_commands(),
                    "error": "Error: Could not save settings. Check folder permissions.",
                    "server_name": get_server_name(),
                },
            )
        return RedirectResponse(url="/manage", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={
                "commands": load_commands(),
                "error": f"Internal Error: {str(e)}",
                "server_name": get_server_name(),
            },
        )


@app.get("/manage")
def manage(request: Request, _=Depends(check_auth)):
    commands = load_commands()
    return templates.TemplateResponse(
        request=request,
        name="manage.html",
        context={"commands": commands, "server_name": get_server_name()},
    )


@app.post("/run")
def run_command(request: Request, command: str = Form(...), _=Depends(check_auth)):
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
                "server_name": get_server_name(),
            },
        )

    # 2. Get the actual command string and split it safely
    actual_cmd_string = commands_dict[command]["cmd"]
    cmd_list = shlex.split(actual_cmd_string)
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
            "server_name": get_server_name(),
        },
    )


@app.websocket("/ws/run/{command}")
async def websocket_run(websocket: WebSocket, command: str):
    await websocket.accept()
    if websocket.cookies.get("lucius_auth") != "ok":
        await websocket.send_text("Error: Unauthorized")
        await websocket.close()
        return

    commands_dict = load_commands()
    if command not in commands_dict:
        await websocket.send_text("Security Error: Unauthorized command.")
        await websocket.close()
        return

    actual_cmd_string = commands_dict[command]["cmd"]
    cmd_list = shlex.split(actual_cmd_string)

    await websocket.send_text(f"$ {actual_cmd_string}\n")

    full_output = []
    output_size = 0
    MAX_LOG_SIZE = 50000  # 50 KB max log memory per command

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_list, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )

        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded_line = line.decode("utf-8", errors="replace")

            # Keep memory bounded
            if output_size < MAX_LOG_SIZE:
                full_output.append(decoded_line)
                output_size += len(decoded_line)
            elif output_size == MAX_LOG_SIZE:
                full_output.append("\n...[Output truncated for history log]...\n")
                output_size += 1  # prevent further appends

            await websocket.send_text(decoded_line)

        await process.wait()

        if process.returncode == 0:
            append_log(command, actual_cmd_string, True, "".join(full_output))
            await websocket.send_text(f"\n[Process exited with code 0]")
        else:
            append_log(command, actual_cmd_string, False, "".join(full_output))
            await websocket.send_text(
                f"\n[Process exited with code {process.returncode}]"
            )

    except Exception as e:
        err_msg = str(e)
        append_log(command, actual_cmd_string, False, err_msg)
        await websocket.send_text(f"\nError executing command: {err_msg}")

    await websocket.close()


@app.post("/add")
def add_command(
    request: Request, name: str = Form(...), cmd: str = Form(...), confirm: str = Form(None), _=Depends(check_auth)
):
    name = name.strip()
    cmd = cmd.strip()
    is_confirm = confirm == "on"

    # 1. Validate name: no spaces, only alphanumerics and underscores
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={
                "commands": load_commands(),
                "error": "Error: Name can only contain letters, numbers, and underscores.",
                "server_name": get_server_name(),
            },
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
                "server_name": get_server_name(),
            },
        )

    # Save new command
    commands[name] = {"cmd": cmd, "enabled": True, "confirm": is_confirm}
    save_commands(commands)

    # GET Redirect to /manage to reload the page
    return RedirectResponse(url="/manage", status_code=303)


@app.post("/delete")
def delete_command(request: Request, name: str = Form(...), _=Depends(check_auth)):
    commands = load_commands()
    if name in commands:
        del commands[name]
        save_commands(commands)

    return RedirectResponse(url="/manage", status_code=303)


@app.post("/edit")
def edit_command(
    request: Request,
    name: str = Form(...),
    cmd: str = Form(...),
    old_name: str = Form(...),
    confirm: str = Form(None),
    _=Depends(check_auth),
):
    name = name.strip()
    cmd = cmd.strip()
    is_confirm = confirm == "on"

    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={
                "commands": load_commands(),
                "error": "Error: Name can only contain letters, numbers, and underscores.",
                "server_name": get_server_name(),
            },
        )

    commands = load_commands()

    if old_name not in commands:
        return RedirectResponse(url="/manage", status_code=303)

    if name != old_name and name in commands:
        return templates.TemplateResponse(
            request=request,
            name="manage.html",
            context={
                "commands": commands,
                "error": f"Error: A command named '{name}' already exists.",
                "server_name": get_server_name(),
            },
        )

    # Preserve key order while replacing old_name with name
    new_commands = {}
    for k, v in commands.items():
        if k == old_name:
            new_commands[name] = {
                "cmd": cmd,
                "enabled": commands.get(old_name, {}).get("enabled", True),
                "confirm": is_confirm,
            }
        else:
            new_commands[k] = v
    save_commands(new_commands)

    return RedirectResponse(url="/manage", status_code=303)


@app.post("/toggle")
def toggle_command(request: Request, name: str = Form(...), _=Depends(check_auth)):
    commands = load_commands()
    if name in commands:
        commands[name]["enabled"] = not commands[name].get("enabled", True)
        save_commands(commands)
    return RedirectResponse(url=f"/manage#cmd-{name}", status_code=303)


@app.post("/reorder")
async def reorder_commands(request: Request, _=Depends(check_auth)):
    content_type = request.headers.get("content-type", "")
    commands = load_commands()
    keys = list(commands.keys())

    # Drag-and-drop JSON payload
    if "application/json" in content_type:
        try:
            data = await request.json()
            new_order = data.get("order", [])
            if isinstance(new_order, list) and new_order:
                reordered = {}
                for k in new_order:
                    if k in commands:
                        reordered[k] = commands[k]
                for k, v in commands.items():
                    if k not in reordered:
                        reordered[k] = v
                save_commands(reordered)
                return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        return {"status": "bad_request"}

    # Standard Form submission (Arrow buttons)
    form = await request.form()
    name = form.get("name")
    direction = form.get("direction")

    if name in keys:
        idx = keys.index(name)
        if direction == "up" and idx > 0:
            keys[idx], keys[idx - 1] = keys[idx - 1], keys[idx]
        elif direction == "down" and idx < len(keys) - 1:
            keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]

        reordered = {k: commands[k] for k in keys}
        save_commands(reordered)

    return RedirectResponse(url=f"/manage#cmd-{name}", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
