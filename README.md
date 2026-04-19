# ⚡ Lucius

**Un tool web elegante in Python per lanciare comandi shell customizzati sul tuo Raspberry Pi o server locale da qualsiasi dispositivo.**

![Lucius Demo](assets/demo.webp)

## 🛠️ Tech Stack
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white)
![Jinja](https://img.shields.io/badge/Jinja-B41717?style=for-the-badge&logo=jinja&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=Raspberry%20Pi&logoColor=white)

## ✨ Features
* 📱 **Design Mobile-First ed Elegante**: Interfaccia web responsiva e pulitissima ispirata ai design tech più moderni.
* 🚀 **Azioni Rapide**: Esegui script bash, riavvia servizi, pulisci la cache, tutto con un solo tap. Nessun terminale SSH richiesto.
* 🛡️ **Sicurezza**: Autenticazione tramite PIN (`.env`) e Whitelist rigorosa per i comandi (niente shell-injection).
* ⚙️ **Gestione Dinamica**: Aggiungi, modifica o elimina i tuoi comandi personalizzati direttamente dall'interfaccia web.

## 🚀 Quick Start

1. **Clona la repository**
   ```bash
   git clone https://github.com/TUO_USERNAME/lucius.git
   cd lucius
   ```

2. **Crea l'ambiente e installa le dipendenze**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Imposta il PIN di sicurezza**
   Crea un file `.env` basato sull'esempio:
   ```bash
   echo "LUCIUS_PIN=1234" > .env
   ```

4. **Avvia il server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   Apri `http://tuo-indirizzo-ip:8000` nel browser e accedi con il PIN!

## 📁 Struttura Cartelle
* `main.py` - Logica core di FastAPI e routing.
* `commands.json` - Il tuo "database" locale dei comandi salvati.
* `lucius.service` - Template systemd per eseguire l'app all'avvio in background.
* `templates/` - File HTML (Jinja2) per il rendering delle interfacce.
* `static/` - File CSS per lo styling.
* `.env` - (da creare) Contiene il PIN segreto.

## 🔒 Sicurezza e Best Practices
Lucius è progettato per girare nella tua **rete locale (LAN)**. 
* L'accesso è protetto dal `LUCIUS_PIN` definito nel file `.env`.
* Il backend accetta ed esegue **solo** i comandi definiti e salvati nell'interfaccia di gestione (Whitelist). Un utente non può passare ed eseguire comandi arbitrari non registrati.
