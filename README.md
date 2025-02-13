# Agent Starter Kit

This is a starter kit for building agents. It is a collection of tools and utilities that make it easier to build agents.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Junyi-99/agent-starter-kit
cd agent-starter-kit
```

### 2. Install the dependencies

```bash
conda create -n agent python=3.13
conda activate agent
pip install uv # we use uv as the package manager.
uv pip install -r pyproject.toml # It's very fast.
```

### 3. Run the project

```bash

```

## Contribution

### Before Push

```bash
python3 -m mypy src 
```
