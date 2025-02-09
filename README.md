# Agent Starter Kit

This is a starter kit for building agents. It is a collection of tools and utilities that make it easier to build agents.

## Installation

### 0. Prerequisites

We recommend using uv to install the dependencies.

```bash
wget -qO- https://astral.sh/uv/install.sh | sh # Install uv
uv python install 3.13
```

### 1. Clone the repository

```bash
git clone https://github.com/Junyi-99/agent-starter-kit
cd agent-starter-kit
```

### 2. Install the dependencies

```bash
uv venv # Create a virtual environment for the project
source .venv/bin/activate

uv sync # Install the dependencies
uv run playwright install # Install playwright for web scraping
```

### 3. Run the project

```bash
uv run python main.py
```
