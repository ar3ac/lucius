# Contributing to Lucius

First off, thank you for considering contributing to Lucius! It's people like you that make Lucius such a great tool.

## How to contribute

### Reporting Bugs
If you find a bug, please create an issue on GitHub and include:
* Your operating system (e.g., Ubuntu 22.04, Raspberry Pi OS)
* The command you ran (if applicable)
* What you expected to happen
* What actually happened (including screenshots if possible)

### Suggesting Enhancements
We welcome feature requests! Please create an issue explaining:
* The problem you're trying to solve
* Your proposed solution or feature

### Pull Requests
1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## Development Setup
If you want to modify the code locally:
1. Clone your fork
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with `LUCIUS_PIN=1234`
4. Run the development server: `uvicorn main:app --reload`
5. Visit `http://localhost:8000`

Please make sure your code follows standard Python PEP-8 conventions. Thank you!
