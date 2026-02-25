import os
import sys
import json
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import webview
from app import create_app, db

# Configuration file location
CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'BalanceTrack')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'launcher_config.json')

# Handle PyInstaller bundled environment
if getattr(sys, 'frozen', False):
    basedir = sys._MEIPASS
    # Bundle certs
    os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(basedir, 'certifi', 'cacert.pem')
else:
    basedir = os.path.dirname(os.path.abspath(__file__))

def get_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def select_db_location():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("First Run", "Welcome to BalanceTrack! Please select a folder where you want to store your database and application data.")
    folder_selected = filedialog.askdirectory()
    root.destroy()
    return folder_selected

def run_flask(app):
    app.run(host='127.0.0.1', port=5555, debug=False, use_reloader=False)

if __name__ == '__main__':
    config = get_config()
    
    if 'db_path' not in config:
        db_folder = select_db_location()
        if not db_folder:
            sys.exit(0)
        config['db_path'] = os.path.abspath(db_folder)
        save_config(config)
    
    db_path = os.path.join(config['db_path'], 'finance.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    app = create_app()
    
    # Initialize DB in the new location if it doesn't exist
    with app.app_context():
        db.create_all()
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, args=(app,), daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(2)
    
    # Launch Webview
    window = webview.create_window('BalanceTrack', 'http://127.0.0.1:5555', width=1280, height=800, min_size=(1024, 768))
    webview.start()
