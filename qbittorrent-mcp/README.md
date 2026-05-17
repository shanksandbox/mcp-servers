# qBittorrent MCP Server

A fully functional [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that enables AI assistants to manage and monitor qBittorrent through a standardized interface. Control torrents, manage categories, search for content, and monitor transfers - all through natural language.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Torrent Management**: Add, pause, resume, delete, and recheck torrents
- **Organization**: Manage categories and tags
- **Search Integration**: Use qBittorrent's built-in search plugins
- **Speed Control**: Set global and per-torrent upload/download limits
- **Monitoring**: View transfer statistics, tracker info, and file lists
- **Resource Access**: Browse torrents, categories, and tags as MCP resources
- **Prompts**: Get formatted summaries of torrent status
- **Auto-authentication**: Handles session management and re-authentication

## Prerequisites

- Python 3.10 or higher
- qBittorrent 4.4+ with Web UI enabled
- MCP-compatible client (Claude Desktop, Cline, etc.)

## Quick Start

### 1. Enable qBittorrent Web UI

1. Open qBittorrent → **Tools** → **Options** → **Web UI**
2. Enable **"Web User Interface (Remote control)"**
3. Set username and password (default port: `8080`)

### 2. Install Dependencies

```bash
pip install mcp httpx