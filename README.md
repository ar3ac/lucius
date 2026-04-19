# ⚡ Lucius

**An elegant Python web tool to launch custom shell commands on your Raspberry Pi or local server from any device.**

![Lucius Demo](assets/demo.webp)

## 🛠️ Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)
![Jinja](https://img.shields.io/badge/Jinja-B41717?style=for-the-badge&logo=jinja&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)

## ✨ Features
* 📱 **Mobile-First Elegant Design**: A responsive, clean web interface inspired by modern tech designs.
* 🚀 **Quick Actions**: Execute bash scripts, restart services, clear caches, all with a single tap. No SSH terminal required.
* 🛡️ **Security**: PIN authentication (`.env`) and strict Command Whitelisting (no shell injection possible).
* ⚙️ **Dynamic Management**: Add, edit, or delete your custom commands directly from the web interface.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/ar3ac/lucius.git
   cd lucius
   ```

2. **Create the environment and install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set the security PIN**
   Create a `.env` file based on the example:
   ```bash
   echo "LUCIUS_PIN=1234" > .env
   ```

4. **Start the server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   Open `http://your-ip-address:8000` in your browser and login with the PIN!

## 📁 Folder Structure
* `main.py` - Core FastAPI logic and routing.
* `commands.json` - Your local "database" of saved commands.
* `lucius.service` - Systemd template to run the app in the background on startup.
* `templates/` - HTML files (Jinja2) for rendering interfaces.
* `static/` - CSS file for styling.
* `.env` - (to be created) Contains the secret PIN.

## 🔒 Security and Best Practices
Lucius is designed to run in your **Local Area Network (LAN)**. 
* Access is protected by the `LUCIUS_PIN` defined in the `.env` file.
* The backend **only** accepts and executes commands defined and saved in the management interface (Whitelist). A user cannot pass and execute arbitrary unregistered commands.
