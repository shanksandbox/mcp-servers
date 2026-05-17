# qbittorrent_mcp_server.py
"""
MCP Server for qBittorrent - Full-featured torrent management
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qbittorrent-mcp")

class QBittorrentClient:
    """Async qBittorrent API client"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cookies = None
    
    async def login(self) -> bool:
        """Authenticate with qBittorrent"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v2/auth/login",
                data={
                    "username": self.username,
                    "password": self.password
                }
            )
            if response.status_code == 200 and response.text == "Ok.":
                self.cookies = response.cookies
                return True
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to qBittorrent API"""
        if not self.cookies:
            await self.login()
        
        url = urljoin(self.base_url, f"/api/v2/{endpoint}")
        
        try:
            response = await self.client.request(
                method, url, cookies=self.cookies, **kwargs
            )
            response.raise_for_status()
            
            # Handle different response types
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            elif response.text:
                return {"status": response.text}
            return {"status": "ok"}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                # Try to re-login
                if await self.login():
                    response = await self.client.request(
                        method, url, cookies=self.cookies, **kwargs
                    )
                    response.raise_for_status()
                    if response.headers.get('content-type', '').startswith('application/json'):
                        return response.json()
                    return {"status": response.text}
            raise
    
    # Torrent Management Methods
    
    async def get_torrents(self, filter: str = "all", category: str = "",
                          sort: str = "", reverse: bool = False,
                          limit: int = 0, offset: int = 0,
                          hashes: str = "") -> List[Dict]:
        """Get list of torrents"""
        params = {
            "filter": filter,
            "category": category,
            "sort": sort,
            "reverse": reverse,
            "limit": limit,
            "offset": offset,
            "hashes": hashes
        }
        return await self._request("GET", "torrents/info", params=params)
    
    async def add_torrent(self, urls: str = "", torrent_files: str = "",
                         savepath: str = "", cookie: str = "",
                         category: str = "", tags: str = "",
                         skip_checking: bool = False,
                         paused: bool = False,
                         root_folder: bool = True,
                         rename: str = "",
                         upload_limit: int = 0,
                         download_limit: int = 0,
                         auto_tmm: bool = False,
                         sequential_download: bool = False,
                         first_last_piece_prio: bool = False) -> Dict:
        """Add new torrent"""
        data = {
            "urls": urls,
            "savepath": savepath,
            "cookie": cookie,
            "category": category,
            "tags": tags,
            "skip_checking": skip_checking,
            "paused": paused,
            "root_folder": root_folder,
            "rename": rename,
            "upLimit": upload_limit,
            "dlLimit": download_limit,
            "autoTMM": auto_tmm,
            "sequentialDownload": sequential_download,
            "firstLastPiecePrio": first_last_piece_prio
        }
        
        # Handle file upload if provided
        files = None
        if torrent_files:
            files = {"torrents": ("file.torrent", torrent_files.encode())}
            return await self._request("POST", "torrents/add", data=data, files=files)
        
        return await self._request("POST", "torrents/add", data=data)
    
    async def pause_torrents(self, hashes: str) -> Dict:
        """Pause torrents"""
        return await self._request("POST", "torrents/pause", data={"hashes": hashes})
    
    async def resume_torrents(self, hashes: str) -> Dict:
        """Resume torrents"""
        return await self._request("POST", "torrents/resume", data={"hashes": hashes})
    
    async def delete_torrents(self, hashes: str, delete_files: bool = False) -> Dict:
        """Delete torrents"""
        return await self._request(
            "POST", "torrents/delete",
            data={"hashes": hashes, "deleteFiles": delete_files}
        )
    
    async def recheck_torrents(self, hashes: str) -> Dict:
        """Recheck torrents"""
        return await self._request("POST", "torrents/recheck", data={"hashes": hashes})
    
    async def set_torrent_location(self, hashes: str, location: str) -> Dict:
        """Set torrent save location"""
        return await self._request(
            "POST", "torrents/setLocation",
            data={"hashes": hashes, "location": location}
        )
    
    async def set_category(self, hashes: str, category: str) -> Dict:
        """Set torrent category"""
        return await self._request(
            "POST", "torrents/setCategory",
            data={"hashes": hashes, "category": category}
        )
    
    async def add_tags(self, hashes: str, tags: str) -> Dict:
        """Add tags to torrents"""
        return await self._request(
            "POST", "torrents/addTags",
            data={"hashes": hashes, "tags": tags}
        )
    
    async def remove_tags(self, hashes: str, tags: str) -> Dict:
        """Remove tags from torrents"""
        return await self._request(
            "POST", "torrents/removeTags",
            data={"hashes": hashes, "tags": tags}
        )
    
    async def set_priority(self, hashes: str, priority: int) -> Dict:
        """Set torrent priority (increase, decrease, top, bottom)"""
        return await self._request(
            "POST", "torrents/setPriority",
            data={"hashes": hashes, "priority": priority}
        )
    
    async def get_torrent_properties(self, hash: str) -> Dict:
        """Get generic properties of a torrent"""
        return await self._request("GET", "torrents/properties", params={"hash": hash})
    
    async def get_torrent_trackers(self, hash: str) -> List[Dict]:
        """Get torrent trackers"""
        return await self._request("GET", "torrents/trackers", params={"hash": hash})
    
    async def get_torrent_webseeds(self, hash: str) -> List[Dict]:
        """Get torrent webseeds"""
        return await self._request("GET", "torrents/webseeds", params={"hash": hash})
    
    async def get_torrent_contents(self, hash: str) -> List[Dict]:
        """Get torrent contents (files)"""
        return await self._request("GET", "torrents/files", params={"hash": hash})
    
    async def get_torrent_pieces(self, hash: str) -> List[int]:
        """Get torrent pieces states"""
        return await self._request("GET", "torrents/pieceStates", params={"hash": hash})
    
    async def get_torrent_hashes(self, hash: str) -> List[str]:
        """Get torrent pieces hashes"""
        return await self._request("GET", "torrents/pieceHashes", params={"hash": hash})
    
    # Transfer Info Methods
    
    async def get_transfer_info(self) -> Dict:
        """Get global transfer info"""
        return await self._request("GET", "transfer/info")
    
    async def get_speed_limits_mode(self) -> Dict:
        """Get speed limits mode"""
        return await self._request("GET", "transfer/speedLimitsMode")
    
    async def toggle_speed_limits_mode(self) -> Dict:
        """Toggle speed limits mode"""
        return await self._request("POST", "transfer/toggleSpeedLimitsMode")
    
    async def get_download_limit(self) -> Dict:
        """Get global download limit"""
        return await self._request("GET", "transfer/downloadLimit")
    
    async def set_download_limit(self, limit: int) -> Dict:
        """Set global download limit (bytes/second)"""
        return await self._request(
            "POST", "transfer/setDownloadLimit",
            data={"limit": limit}
        )
    
    async def get_upload_limit(self) -> Dict:
        """Get global upload limit"""
        return await self._request("GET", "transfer/uploadLimit")
    
    async def set_upload_limit(self, limit: int) -> Dict:
        """Set global upload limit (bytes/second)"""
        return await self._request(
            "POST", "transfer/setUploadLimit",
            data={"limit": limit}
        )
    
    # Category Management
    
    async def get_categories(self) -> Dict:
        """Get all categories"""
        return await self._request("GET", "torrents/categories")
    
    async def create_category(self, category: str, save_path: str = "") -> Dict:
        """Create new category"""
        return await self._request(
            "POST", "torrents/createCategory",
            data={"category": category, "savePath": save_path}
        )
    
    async def edit_category(self, category: str, save_path: str) -> Dict:
        """Edit category"""
        return await self._request(
            "POST", "torrents/editCategory",
            data={"category": category, "savePath": save_path}
        )
    
    async def remove_categories(self, categories: str) -> Dict:
        """Remove categories"""
        return await self._request(
            "POST", "torrents/removeCategories",
            data={"categories": categories}
        )
    
    # Tag Management
    
    async def get_tags(self) -> List[str]:
        """Get all tags"""
        return await self._request("GET", "torrents/tags")
    
    async def create_tags(self, tags: str) -> Dict:
        """Create tags"""
        return await self._request(
            "POST", "torrents/createTags",
            data={"tags": tags}
        )
    
    async def delete_tags(self, tags: str) -> Dict:
        """Delete tags"""
        return await self._request(
            "POST", "torrents/deleteTags",
            data={"tags": tags}
        )
    
    # Search Methods (if search plugin is enabled)
    
    async def start_search(self, pattern: str, plugins: str = "all",
                          category: str = "all") -> Dict:
        """Start search"""
        return await self._request(
            "POST", "search/start",
            data={"pattern": pattern, "plugins": plugins, "category": category}
        )
    
    async def stop_search(self, id: int) -> Dict:
        """Stop search"""
        return await self._request(
            "POST", "search/stop",
            data={"id": id}
        )
    
    async def get_search_status(self, id: int = 0) -> List[Dict]:
        """Get search status"""
        return await self._request("GET", "search/status", params={"id": id})
    
    async def get_search_results(self, id: int, limit: int = 0,
                                offset: int = 0) -> Dict:
        """Get search results"""
        return await self._request(
            "GET", "search/results",
            params={"id": id, "limit": limit, "offset": offset}
        )
    
    async def get_search_plugins(self) -> List[Dict]:
        """Get search plugins"""
        return await self._request("GET", "search/plugins")
    
    async def install_search_plugin(self, sources: str) -> Dict:
        """Install search plugin"""
        return await self._request(
            "POST", "search/installPlugin",
            data={"sources": sources}
        )
    
    async def uninstall_search_plugin(self, names: str) -> Dict:
        """Uninstall search plugins"""
        return await self._request(
            "POST", "search/uninstallPlugin",
            data={"names": names}
        )
    
    async def enable_search_plugin(self, names: str, enable: bool) -> Dict:
        """Enable/disable search plugins"""
        return await self._request(
            "POST", "search/enablePlugin",
            data={"names": names, "enable": enable}
        )
    
    async def update_search_plugins(self) -> Dict:
        """Update search plugins"""
        return await self._request("POST", "search/updatePlugins")
    
    # App/Settings Methods
    
    async def get_app_version(self) -> str:
        """Get application version"""
        return await self._request("GET", "app/version")
    
    async def get_api_version(self) -> str:
        """Get API version"""
        return await self._request("GET", "app/webapiVersion")
    
    async def get_build_info(self) -> Dict:
        """Get build info"""
        return await self._request("GET", "app/buildInfo")
    
    async def shutdown(self) -> Dict:
        """Shutdown qBittorrent"""
        return await self._request("POST", "app/shutdown")
    
    async def get_preferences(self) -> Dict:
        """Get application preferences"""
        return await self._request("GET", "app/preferences")
    
    async def set_preferences(self, prefs: Dict) -> Dict:
        """Set application preferences"""
        return await self._request(
            "POST", "app/setPreferences",
            json=prefs
        )
    
    async def get_default_save_path(self) -> Dict:
        """Get default save path"""
        return await self._request("GET", "app/defaultSavePath")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# MCP Server Setup
app = Server("qbittorrent-mcp")

# Configuration
config = {
    "base_url": "http://localhost:8080",
    "username": "admin",
    "password": "adminadmin"
}

# Initialize client
qbt = QBittorrentClient(
    config["base_url"],
    config["username"],
    config["password"]
)

@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="qbittorrent://torrents/active",
            name="Active Torrents",
            description="Currently active torrents",
            mimeType="application/json"
        ),
        Resource(
            uri="qbittorrent://torrents/all",
            name="All Torrents",
            description="All torrents in the client",
            mimeType="application/json"
        ),
        Resource(
            uri="qbittorrent://transfer/info",
            name="Transfer Info",
            description="Global transfer information",
            mimeType="application/json"
        ),
        Resource(
            uri="qbittorrent://categories",
            name="Categories",
            description="All torrent categories",
            mimeType="application/json"
        ),
        Resource(
            uri="qbittorrent://tags",
            name="Tags",
            description="All torrent tags",
            mimeType="application/json"
        ),
        Resource(
            uri="qbittorrent://settings",
            name="Settings",
            description="Application preferences",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource"""
    try:
        if not qbt.cookies:
            await qbt.login()
        
        if uri == "qbittorrent://torrents/active":
            data = await qbt.get_torrents(filter="active")
        elif uri == "qbittorrent://torrents/all":
            data = await qbt.get_torrents(filter="all")
        elif uri == "qbittorrent://transfer/info":
            data = await qbt.get_transfer_info()
        elif uri == "qbittorrent://categories":
            data = await qbt.get_categories()
        elif uri == "qbittorrent://tags":
            data = await qbt.get_tags()
        elif uri == "qbittorrent://settings":
            data = await qbt.get_preferences()
        else:
            raise ValueError(f"Unknown resource: {uri}")
        
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="add_torrent",
            description="Add a new torrent from URL or magnet link",
            inputSchema={
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "string",
                        "description": "URL or magnet link (multiple separated by newline)"
                    },
                    "savepath": {
                        "type": "string",
                        "description": "Save path for the torrent"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category for the torrent"
                    },
                    "paused": {
                        "type": "boolean",
                        "description": "Add in paused state",
                        "default": False
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags"
                    }
                },
                "required": ["urls"]
            }
        ),
        Tool(
            name="pause_torrents",
            description="Pause active torrents",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashes": {
                        "type": "string",
                        "description": "Torrent hashes separated by | (or 'all')"
                    }
                },
                "required": ["hashes"]
            }
        ),
        Tool(
            name="resume_torrents",
            description="Resume paused torrents",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashes": {
                        "type": "string",
                        "description": "Torrent hashes separated by | (or 'all')"
                    }
                },
                "required": ["hashes"]
            }
        ),
        Tool(
            name="delete_torrents",
            description="Delete torrents (optionally with files)",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashes": {
                        "type": "string",
                        "description": "Torrent hashes separated by |"
                    },
                    "delete_files": {
                        "type": "boolean",
                        "description": "Also delete downloaded files",
                        "default": False
                    }
                },
                "required": ["hashes"]
            }
        ),
        Tool(
            name="set_category",
            description="Set category for torrents",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashes": {
                        "type": "string",
                        "description": "Torrent hashes separated by |"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category name"
                    }
                },
                "required": ["hashes", "category"]
            }
        ),
        Tool(
            name="add_tags",
            description="Add tags to torrents",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashes": {
                        "type": "string",
                        "description": "Torrent hashes separated by |"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags"
                    }
                },
                "required": ["hashes", "tags"]
            }
        ),
        Tool(
            name="set_global_limits",
            description="Set global upload/download speed limits",
            inputSchema={
                "type": "object",
                "properties": {
                    "download_limit": {
                        "type": "integer",
                        "description": "Download limit in bytes/second (0 for unlimited)"
                    },
                    "upload_limit": {
                        "type": "integer",
                        "description": "Upload limit in bytes/second (0 for unlimited)"
                    }
                }
            }
        ),
        Tool(
            name="search_torrents",
            description="Search for torrents using qBittorrent search plugins",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern"
                    },
                    "plugins": {
                        "type": "string",
                        "description": "Search plugins (default: all)",
                        "default": "all"
                    },
                    "category": {
                        "type": "string",
                        "description": "Search category",
                        "default": "all"
                    }
                },
                "required": ["pattern"]
            }
        ),
        Tool(
            name="manage_categories",
            description="Create, edit, or remove categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "edit", "remove"],
                        "description": "Action to perform"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category name"
                    },
                    "save_path": {
                        "type": "string",
                        "description": "Save path for the category"
                    }
                },
                "required": ["action", "category"]
            }
        ),
        Tool(
            name="get_torrent_details",
            description="Get detailed information about a specific torrent",
            inputSchema={
                "type": "object",
                "properties": {
                    "hash": {
                        "type": "string",
                        "description": "Torrent hash"
                    },
                    "include_trackers": {
                        "type": "boolean",
                        "description": "Include tracker information",
                        "default": True
                    },
                    "include_files": {
                        "type": "boolean",
                        "description": "Include file list",
                        "default": True
                    }
                },
                "required": ["hash"]
            }
        ),
        Tool(
            name="recheck_torrents",
            description="Force recheck torrents",
            inputSchema={
                "type": "object",
                "properties": {
                    "hashes": {
                        "type": "string",
                        "description": "Torrent hashes separated by |"
                    }
                },
                "required": ["hashes"]
            }
        ),
        Tool(
            name="toggle_speed_limits",
            description="Toggle alternative speed limits",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""
    try:
        if not qbt.cookies:
            await qbt.login()
        
        result = None
        
        if name == "add_torrent":
            result = await qbt.add_torrent(
                urls=arguments.get("urls", ""),
                savepath=arguments.get("savepath", ""),
                category=arguments.get("category", ""),
                paused=arguments.get("paused", False),
                tags=arguments.get("tags", "")
            )
        
        elif name == "pause_torrents":
            result = await qbt.pause_torrents(arguments["hashes"])
        
        elif name == "resume_torrents":
            result = await qbt.resume_torrents(arguments["hashes"])
        
        elif name == "delete_torrents":
            result = await qbt.delete_torrents(
                arguments["hashes"],
                arguments.get("delete_files", False)
            )
        
        elif name == "set_category":
            result = await qbt.set_category(
                arguments["hashes"],
                arguments["category"]
            )
        
        elif name == "add_tags":
            result = await qbt.add_tags(
                arguments["hashes"],
                arguments["tags"]
            )
        
        elif name == "set_global_limits":
            if "download_limit" in arguments:
                await qbt.set_download_limit(arguments["download_limit"])
            if "upload_limit" in arguments:
                await qbt.set_upload_limit(arguments["upload_limit"])
            result = {"status": "Speed limits updated"}
        
        elif name == "search_torrents":
            result = await qbt.start_search(
                pattern=arguments["pattern"],
                plugins=arguments.get("plugins", "all"),
                category=arguments.get("category", "all")
            )
        
        elif name == "manage_categories":
            action = arguments["action"]
            category = arguments["category"]
            save_path = arguments.get("save_path", "")
            
            if action == "create":
                result = await qbt.create_category(category, save_path)
            elif action == "edit":
                result = await qbt.edit_category(category, save_path)
            elif action == "remove":
                result = await qbt.remove_categories(category)
        
        elif name == "get_torrent_details":
            hash_val = arguments["hash"]
            details = await qbt.get_torrent_properties(hash_val)
            
            if arguments.get("include_trackers", True):
                details["trackers"] = await qbt.get_torrent_trackers(hash_val)
            
            if arguments.get("include_files", True):
                details["files"] = await qbt.get_torrent_contents(hash_val)
            
            result = details
        
        elif name == "recheck_torrents":
            result = await qbt.recheck_torrents(arguments["hashes"])
        
        elif name == "toggle_speed_limits":
            result = await qbt.toggle_speed_limits_mode()
        
        if result is not None:
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Unknown tool"})
            )]
    
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]

@app.list_prompts()
async def list_prompts() -> list:
    """List available prompts"""
    return [
        types.Prompt(
            name="torrent_status",
            description="Get summary of torrent status",
            arguments=[
                types.PromptArgument(
                    name="filter",
                    description="Torrent filter (all, downloading, completed, etc.)",
                    required=False
                )
            ]
        )
    ]

@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    """Generate prompt content"""
    if name == "torrent_status":
        filter_type = arguments.get("filter", "all")
        torrents = await qbt.get_torrents(filter=filter_type)
        transfer = await qbt.get_transfer_info()
        
        return types.GetPromptResult(
            description=f"Torrent status - {filter_type} filter",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Current qBittorrent Status:

Transfer Info:
- Download Speed: {transfer.get('dl_info_speed', 0) / 1024 / 1024:.2f} MB/s
- Upload Speed: {transfer.get('up_info_speed', 0) / 1024 / 1024:.2f} MB/s
- Connected: {transfer.get('dht_nodes', 0)} nodes

Torrents ({len(torrents)}):
{json.dumps(torrents, indent=2)}
"""
                    )
                )
            ]
        )
    
    raise ValueError(f"Unknown prompt: {name}")

async def main():
    """Main entry point"""
    logger.info("Starting qBittorrent MCP server...")
    
    # Test connection
    if await qbt.login():
        version = await qbt.get_app_version()
        logger.info(f"Connected to qBittorrent {version}")
    else:
        logger.error("Failed to connect to qBittorrent")
        return
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationCapabilities(
                sampling={},
                experimental={},
                roots={}
            ),
            notification_options=NotificationOptions(
                tools_changed=False,
                resources_changed=False,
                prompts_changed=False
            )
        )

if __name__ == "__main__":
    asyncio.run(main())