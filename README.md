# ⚙️ Setup Guide — Google Drive FastMCP Integration

This document walks you through setting up the **Google Drive FastMCP Integration** project — from installation to authentication and verification.

---

## 🧩 1. Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.9 or later installed  
- ✅ pip (Python package manager)  
- ✅ A Google account  
- ✅ Access to [Google Cloud Console](https://console.cloud.google.com/)  

---

## 📦 2. Clone the Repository

```bash
git clone https://github.com/<your-username>/google-drive-fastmcp.git
cd google-drive-fastmcp
```

---

## 🧰 3. Create a Virtual Environment

It’s best practice to isolate project dependencies using a virtual environment.

```bash
python -m venv venv
```

Activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

---

## 📦 4. Install Dependencies

Install all dependencies from the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

If you prefer to install them manually, use:

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 fastmcp httplib2 requests typing-extensions
```

---

## 🔑 5. Enable Google Drive API

1. Go to [Google Cloud Console](https://console.cloud.google.com/).  
2. Create a **new project** (or select an existing one).  
3. Navigate to **APIs & Services → Library**.  
4. Search for **Google Drive API**.  
5. Click **Enable**.

---

## 🧾 6. Create OAuth2 Credentials

1. In Google Cloud Console, go to **APIs & Services → Credentials**.  
2. Click **Create Credentials → OAuth client ID**.  
3. Choose **Desktop App** as the application type.  
4. Download the file named `credentials.json`.  
5. Place it in the same directory as your main script (`google_drive_mcp.py`).

---

## 🔐 7. Authenticate with Google

Run the main script once to trigger authentication:

```bash
python google_drive_mcp.py
```

You’ll see a message like:

```
Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?...
```

A browser window will open — sign in with your Google account and grant permission.

After authentication, a file named:

```
.google_drive_token.pickle
```

will be created in your home directory (for example, `C:\Users\<User>\` on Windows or `~` on macOS/Linux).  
This stores your access token securely for reuse.

---

## 🧩 8. Verify Setup

Once authenticated, you can verify everything works by listing your Drive files:

```bash
python -c "from google_drive_mcp import list_drive_files; print(list_drive_files(3))"
```

If successful, you’ll see output like:

```
Found 3 files:

1. backup_report.pdf
   ID: 1xYzAbc1234
   Link: https://drive.google.com/file/d/1xYzAbc1234/view
```

---

## 🧠 9. Common Issues

### ❌ `credentials.json` not found
Ensure the file is in the same directory as your script and named **exactly** `credentials.json`.

### 🔄 Authentication prompt not appearing
Delete the token file and reauthenticate:

**Windows:**
```bash
del %USERPROFILE%\.google_drive_token.pickle
```

**macOS/Linux:**
```bash
rm ~/.google_drive_token.pickle
```

### 📄 Uploaded PDF opens half-screen in Drive
Drive preview mode can restrict view.  
Click **“Open in new window”** or **“Download”** for full-screen view.

---

## 🚀 10. Try It Out

Run these examples after setup:

### Upload a File
```python
from google_drive_mcp import upload_to_drive
print(upload_to_drive("report.pdf"))
```

### List Files
```python
from google_drive_mcp import list_drive_files
print(list_drive_files(5))
```

### Create a Folder
```python
from google_drive_mcp import create_drive_folder
print(create_drive_folder("New_Backups"))
```

Example output:

```
✓ Folder created!
Name: New_Backups
ID: 1AbCdEfGhiJKlmnOPqRstUV
```

---

## 🧩 What is FastMCP?

**FastMCP** (Fast Model Context Protocol) is a Python framework that allows you to expose Python functions as “tools” for AI systems (like ChatGPT or other agents).  
By registering functions with `@mcp.tool()`, you can let an AI call them directly — enabling automation, integration, and intelligent orchestration.

In this project, FastMCP is used to expose the following tools:

| Tool | Description |
|------|--------------|
| `list_drive_files(page_size=10)` | Lists recent Google Drive files |
| `upload_to_drive(file_path, folder_id="")` | Uploads a local file to Drive |
| `create_drive_folder(folder_name, parent_id="")` | Creates a new Drive folder |

---

## 🧾 11. Project Structure

```
google-drive-fastmcp/
│
├── google_drive_mcp.py          # Main script
├── credentials.json             # Google OAuth credentials (user-provided)
├── requirements.txt             # Dependencies list
├── README.md                    # Project overview
└── setup.md                     # Setup and installation guide
```

---

## 📜 License

MIT License © 2025 **Shashank Kumar**

You are free to use, modify, and distribute this project with proper attribution.
