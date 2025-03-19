import gradio as gr
import time
import os
from steamcmd_operations import (
    list_installed_games, get_game_info, 
    download_game, cancel_download, cleanup_failed_download
)
from file_sharing import (
    list_shares, create_share, delete_share, 
    generate_access_url, start_file_server
)

def create_advanced_ui():
    """Create an advanced UI for the SteamCMD Manager"""
    
    active_downloads = {}
    file_server = None
    
    with gr.Blocks() as demo:
        with gr.Row():
            gr.Markdown("# SteamCMD Manager Pro")
        
        with gr.Tabs() as tabs:
            # Library Tab
            with gr.Tab("Game Library"):
                with gr.Row():
                    refresh_library_btn = gr.Button("Refresh Library")
                    add_game_btn = gr.Button("Add New Game")
                
                games_table = gr.Dataframe(
                    headers=["Game", "App ID", "Size", "Path", "Actions"],
                    datatype=["str", "str", "str", "str", "str"],
                    label="Installed Games"
                )
                
                with gr.Row():
                    selected_game_id = gr.Textbox(visible=False)
                    game_details = gr.JSON(label="Game Details")
                
                with gr.Row():
                    update_game_btn = gr.Button("Update Game")
                    share_game_btn = gr.Button("Share Game")
                    delete_game_btn = gr.Button("Delete Game")
                
                def refresh_library():
                    games = list_installed_games()
                    table_data = [
                        [g["name"], g["app_id"], g["size"], g["path"], "Select"] 
                        for g in games
                    ]
                    return table_data
                
                refresh_library_btn.click(refresh_library, None, games_table)
                
                def select_game(evt: gr.SelectData, games):
                    game_row = games[evt.index[0]]
                    app_id = game_row[1]
                    game_info = get_game_info(app_id)
                    return app_id, game_info
                
                games_table.select(select_game, games_table, [selected_game_id, game_details])
            
            # Downloads Tab  
            with gr.Tab("Downloads"):
                with gr.Row():
                    app_id_input = gr.Textbox(label="App ID")
                    search_app_btn = gr.Button("Search")
                
                app_info_display = gr.Markdown("Enter an App ID to see details")
                
                with gr.Row():
                    username = gr.Textbox(label="Username", value="anonymous")
                    password = gr.Textbox(label="Password", type="password", visible=False)
                    anonymous_login = gr.Checkbox(label="Anonymous Login", value=True)
                
                def toggle_password(anonymous):
                    return gr.Textbox.update(visible=not anonymous)
                
                anonymous_login.change(toggle_password, anonymous_login, password)
                
                download_btn = gr.Button("Start Download")
                
                with gr.Row():
                    gr.Markdown("Download Progress:")
                    download_progress = gr.Slider(minimum=0, maximum=100, value=0, step=1)
                    download_status = gr.Textbox(label="Status", value="Ready")
                
                active_downloads_table = gr.Dataframe(
                    headers=["App ID", "Game", "Progress", "Status", "Started", "Actions"],
                    label="Active Downloads"
                )
                
                def start_new_download(app_id, username, password, anonymous):
                    if anonymous:
                        username = "anonymous"
                        password = ""
                    
                    try:
                        game_info = get_game_info(app_id)
                        proc = download_game(app_id, username, password)
                        
                        download_id = str(time.time())
                        active_downloads[download_id] = {
                            "process": proc,
                            "app_id": app_id,
                            "game_name": game_info.get("name", f"Game {app_id}"),
                            "progress": 0,
                            "status": "starting",
                            "start_time": time.strftime("%H:%M:%S")
                        }
                        
                        # Start monitoring in a background thread
                        import threading
                        
                        def monitor_download():
                            while proc.poll() is None:
                                line = proc.stdout.readline()
                                if not line:
                                    break
                                    
                                # Update progress based on output
                                # Implement actual progress parsing here
                                active_downloads[download_id]["progress"] += 1
                                if "Error" in line:
                                    active_downloads[download_id]["status"] = "error"
                                elif "Success" in line:
                                    active_downloads[download_id]["status"] = "completed"
                                    active_downloads[download_id]["progress"] = 100
                                
                                time.sleep(0.1)
                        
                        threading.Thread(target=monitor_download, daemon=True).start()
                        
                        return f"Download started for {game_info.get('name', app_id)}"
                    except Exception as e:
                        return f"Error: {str(e)}"
                
                download_btn.click(
                    start_new_download,
                    inputs=[app_id_input, username, password, anonymous_login],
                    outputs=download_status
                )
                
                def update_downloads_table():
                    rows = []
                    for download_id, download in active_downloads.items():
                        rows.append([
                            download["app_id"],
                            download["game_name"],
                            download["progress"],
                            download["status"],
                            download["start_time"],
                            "Cancel" if download["status"] not in ["completed", "error"] else "Remove"
                        ])
                    return rows
                
                # Auto-refresh the downloads table
                demo.load(update_downloads_table, None, active_downloads_table, every=2)
            
            # Sharing Tab
            with gr.Tab("File Sharing"):
                with gr.Row():
                    server_status = gr.Textbox(label="Server Status", value="Server not running")
                    start_server_btn = gr.Button("Start Server")
                    stop_server_btn = gr.Button("Stop Server")
                
                shares_table = gr.Dataframe(
                    headers=["Share ID", "Game", "Created", "URL", "Actions"],
                    label="Active Shares"
                )
                
                refresh_shares_btn = gr.Button("Refresh Shares")
                
                def refresh_shares():
                    shares = list_shares()
                    rows = []
                    for share in shares:
                        rows.append([
                            share["id"],
                            share["game_name"],
                            time.strftime("%Y-%m-%d %H:%M", time.localtime(share["created_at"])),
                            generate_access_url(share["id"]),
                            "Delete"
                        ])
                    return rows
                
                refresh_shares_btn.click(refresh_shares, None, shares_table)
                
                def start_server():
                    nonlocal file_server
                    if file_server is None or file_server.poll() is not None:
                        try:
                            file_server = start_file_server()
                            return "File server running on port 8000"
                        except Exception as e:
                            return f"Error starting server: {str(e)}"
                    return "Server already running"
                
                start_server_btn.click(start_server, None, server_status)
                
                def stop_server():
                    nonlocal file_server
                    if file_server and file_server.poll() is None:
                        file_server.terminate()
                        return "Server stopped"
                    return "No server running"
                
                stop_server_btn.click(stop_server, None, server_status)
    
    return demo 