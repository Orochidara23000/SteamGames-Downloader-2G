import os
import random
import string
import json
import logging
from pathlib import Path
import shutil
import subprocess

# Configuration
SHARE_DB_FILE = os.path.expanduser("~/steamcmd/shares.json")
SHARE_DIR = os.path.expanduser("~/public_shares")

def ensure_share_dir():
    """Make sure the sharing directory exists"""
    os.makedirs(SHARE_DIR, exist_ok=True)
    if not os.path.exists(SHARE_DB_FILE):
        with open(SHARE_DB_FILE, 'w') as f:
            json.dump([], f)

def generate_share_id():
    """Generate a unique sharing ID"""
    chars = string.ascii_letters + string.digits
    while True:
        share_id = ''.join(random.choice(chars) for _ in range(12))
        if not share_exists(share_id):
            return share_id

def share_exists(share_id):
    """Check if a share ID already exists"""
    try:
        with open(SHARE_DB_FILE, 'r') as f:
            shares = json.load(f)
        return any(share['id'] == share_id for share in shares)
    except:
        return False

def create_share(game_path, game_name, app_id):
    """Create a new share for a game"""
    ensure_share_dir()
    
    share_id = generate_share_id()
    share_path = os.path.join(SHARE_DIR, share_id)
    
    # Create symbolic link instead of copying
    try:
        os.symlink(game_path, share_path)
        
        # Save share information
        share_info = {
            'id': share_id,
            'game_name': game_name,
            'app_id': app_id,
            'created_at': int(time.time()),
            'path': share_path
        }
        
        with open(SHARE_DB_FILE, 'r') as f:
            shares = json.load(f)
        
        shares.append(share_info)
        
        with open(SHARE_DB_FILE, 'w') as f:
            json.dump(shares, f)
            
        return share_info
    except Exception as e:
        logging.error(f"Failed to create share: {str(e)}")
        return None

def delete_share(share_id):
    """Remove a share"""
    try:
        with open(SHARE_DB_FILE, 'r') as f:
            shares = json.load(f)
            
        new_shares = [share for share in shares if share['id'] != share_id]
        
        if len(new_shares) != len(shares):
            # Share found, remove the symlink
            share_path = os.path.join(SHARE_DIR, share_id)
            if os.path.islink(share_path):
                os.unlink(share_path)
                
            with open(SHARE_DB_FILE, 'w') as f:
                json.dump(new_shares, f)
                
            return True
        return False
    except Exception as e:
        logging.error(f"Failed to delete share: {str(e)}")
        return False

def list_shares():
    """List all active shares"""
    ensure_share_dir()
    
    try:
        with open(SHARE_DB_FILE, 'r') as f:
            shares = json.load(f)
        return shares
    except:
        return []

def generate_access_url(share_id, host='localhost', port=8000):
    """Generate a URL for accessing the share"""
    return f"http://{host}:{port}/share/{share_id}"

def start_file_server(port=8000):
    """Start a simple HTTP server for file sharing"""
    # Using Python's built-in HTTP server
    server_proc = subprocess.Popen([
        "python3", "-m", "http.server", str(port)
    ], cwd=SHARE_DIR)
    
    return server_proc 