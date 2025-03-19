import os
import logging
import gradio as gr
from steamcmd_operations import check_steamcmd, install_steamcmd, ensure_directories
from advanced_ui import create_advanced_ui

# Logging setup
logging.basicConfig(
    filename='steamcmd_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main application entry point"""
    # Ensure required directories exist
    ensure_directories()
    
    # Check SteamCMD installation
    steam_installed = check_steamcmd()
    
    if not steam_installed:
        print("SteamCMD not found. Installing...")
        result = install_steamcmd()
        if check_steamcmd():
            print("SteamCMD installed successfully.")
        else:
            print("SteamCMD installation failed!")
            return
    
    # Create and launch the UI
    app = create_advanced_ui()
    app.launch()

if __name__ == "__main__":
    main()