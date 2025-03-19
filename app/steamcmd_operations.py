import os
import subprocess
import logging
import re
import time
import shutil
from pathlib import Path

# Configuration
STEAMCMD_DIR = os.path.expanduser("~/steamcmd")
GAMES_DIR = os.path.expanduser("~/steam_games")
STEAMCMD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"

def ensure_directories():
    """Ensure all needed directories exist"""
    for directory in [STEAMCMD_DIR, GAMES_DIR]:
        os.makedirs(directory, exist_ok=True)
    logging.info(f"Required directories verified: {STEAMCMD_DIR}, {GAMES_DIR}")

def check_steamcmd():
    """Verify SteamCMD installation status"""
    if os.path.exists(os.path.join(STEAMCMD_DIR, "steamcmd.sh")):
        logging.info("SteamCMD installation verified")
        return True
    else:
        logging.warning("SteamCMD not found")
        return False

def install_steamcmd():
    """Install SteamCMD (fallback action)"""
    if not os.path.exists(STEAMCMD_DIR):
        os.makedirs(STEAMCMD_DIR)
    # Download and extract
    logging.info("Installing SteamCMD...")
    try:
        subprocess.run([
            "wget", STEAMCMD_URL, 
            "-P", STEAMCMD_DIR
        ], check=True)
        subprocess.run([
            "tar", "-xvzf", os.path.join(STEAMCMD_DIR, "steamcmd_linux.tar.gz"),
            "-C", STEAMCMD_DIR
        ], check=True)
        logging.info("SteamCMD installed successfully")
        return "SteamCMD installed successfully"
    except subprocess.CalledProcessError as e:
        error_msg = f"Installation failed: {str(e)}"
        logging.error(error_msg)
        return error_msg

# Game storage paths
def get_game_path(app_id):
    """Get the installation path for a specific game"""
    return os.path.join(GAMES_DIR, f"app_{app_id}")

def get_game_info(app_id):
    """Get information about a Steam game"""
    cmd = [
        os.path.join(STEAMCMD_DIR, "steamcmd.sh"),
        "+login", "anonymous",
        "+app_info_print", app_id,
        "+quit"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output to extract game name
        output = result.stdout
        name_match = re.search(r'"common"\s*{[^}]*"name"\s*"([^"]*)"', output)
        
        if name_match:
            return {
                "name": name_match.group(1),
                "app_id": app_id
            }
        return {"name": f"Unknown Game ({app_id})", "app_id": app_id}
    except Exception as e:
        logging.error(f"Failed to get game info: {str(e)}")
        return {"name": f"Unknown Game ({app_id})", "app_id": app_id}

def download_game(app_id, username="anonymous", password="", install_dir=None):
    """Download or update a Steam game"""
    if install_dir is None:
        install_dir = get_game_path(app_id)
    
    os.makedirs(install_dir, exist_ok=True)
    
    cmd = [
        os.path.join(STEAMCMD_DIR, "steamcmd.sh"),
        "+login", username, password,
        "+force_install_dir", install_dir,
        "+app_update", app_id, "validate",
        "+quit"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    return proc

def cancel_download(proc):
    """Cancel an active download"""
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return True
    return False

def cleanup_failed_download(app_id):
    """Remove partially downloaded files"""
    install_dir = get_game_path(app_id)
    if os.path.exists(install_dir):
        try:
            shutil.rmtree(install_dir)
            return True
        except:
            logging.error(f"Failed to remove directory: {install_dir}")
            return False
    return True

def list_installed_games():
    """List all games installed through this manager"""
    if not os.path.exists(GAMES_DIR):
        return []
    
    games = []
    app_id_pattern = re.compile(r"app_(\d+)")
    
    for item in os.listdir(GAMES_DIR):
        match = app_id_pattern.match(item)
        if match and os.path.isdir(os.path.join(GAMES_DIR, item)):
            app_id = match.group(1)
            info = get_game_info(app_id)
            size = get_directory_size(os.path.join(GAMES_DIR, item))
            games.append({
                "app_id": app_id,
                "name": info["name"],
                "size": format_size(size),
                "path": os.path.join(GAMES_DIR, item)
            })
    
    return games

def get_directory_size(path):
    """Calculate total size of a directory in bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def format_size(size_bytes):
    """Format bytes to human-readable size"""
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}" 