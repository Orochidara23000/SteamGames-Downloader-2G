import gradio as gr
import time
import os
from steamcmd_operations import list_installed_games, get_game_info, download_game

def create_advanced_ui():
    """Create a simple UI for the SteamCMD Manager"""
    
    with gr.Blocks() as demo:
        gr.Markdown("# SteamCMD Manager")
        
        with gr.Tab("Download Games"):
            app_id = gr.Textbox(label="Enter Steam App ID (e.g., 730 for CS:GO)")
            username = gr.Textbox(label="Username", value="anonymous")
            password = gr.Textbox(label="Password", type="password")
            anonymous = gr.Checkbox(label="Anonymous Login", value=True)
            
            download_btn = gr.Button("Start Download")
            status = gr.Textbox(label="Status", value="Ready")
            
            def on_anonymous_change(anon):
                if anon:
                    return gr.Textbox.update(value="anonymous", interactive=False), gr.Textbox.update(value="", interactive=False)
                else:
                    return gr.Textbox.update(interactive=True), gr.Textbox.update(interactive=True)
            
            anonymous.change(on_anonymous_change, anonymous, [username, password])
            
            def start_download(app_id, user, pwd, anon):
                if not app_id.strip():
                    return "Please enter a valid App ID"
                
                try:
                    if anon:
                        user = "anonymous" 
                        pwd = ""
                        
                    # Get game info
                    info = get_game_info(app_id)
                    game_name = info.get("name", f"Game {app_id}")
                    
                    # Start download process
                    proc = download_game(app_id, user, pwd)
                    
                    # This would normally be more complex with threading
                    return f"Started download for {game_name} (App ID: {app_id})"
                except Exception as e:
                    return f"Error: {str(e)}"
            
            download_btn.click(start_download, [app_id, username, password, anonymous], status)
        
        with gr.Tab("Game Library"):
            refresh_btn = gr.Button("Refresh Game List")
            games_list = gr.Dataframe(
                headers=["Game", "App ID", "Size", "Path"],
                label="Installed Games"
            )
            
            def refresh_games():
                games = list_installed_games()
                return [[g["name"], g["app_id"], g["size"], g["path"]] for g in games]
            
            refresh_btn.click(refresh_games, None, games_list)
        
        with gr.Tab("About"):
            gr.Markdown("""
            ## SteamCMD Manager
            
            This is a simple GUI for managing SteamCMD downloads.
            
            ### Features:
            - Download Steam games using SteamCMD
            - Manage your game library
            - Anonymous and account-based downloads
            
            ### Usage:
            1. Enter the App ID of the game you want to download
            2. Choose login method (anonymous or with credentials)
            3. Click "Start Download"
            4. Check the Library tab to see installed games
            """)
    
    return demo 