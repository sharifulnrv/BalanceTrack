import PyInstaller.__main__
import os
import sys
import certifi

def build():
    # Application name
    app_name = "BalanceTrack"
    
    # Path to the main entry point
    entry_point = "launcher.py"
    
    # Static and template folders
    # Note: Using ; for Windows, : for Linux/Mac
    separator = ";" if sys.platform == "win32" else ":"
    
    
    add_data = [
        (f"app/templates", "app/templates"),
        (f"app/static", "app/static"),
        (certifi.where(), "certifi"),
        (".env", "."),
    ]
    
    # Explicitly find and add Tcl/Tk data because PyInstaller 6.x on Python 3.13 
    # sometimes fails to find them automatically on Windows.
    python_dir = os.path.dirname(sys.executable)
    # Check both virtualenv and base python installation
    tcl_paths = [
        os.path.join(python_dir, "tcl"),
        os.path.join(os.path.dirname(python_dir), "tcl"), # If in venv
        r"C:\Program Files\Python313\tcl" # Fallback to known location
    ]
    
    tcl_found = False
    for p in tcl_paths:
        if os.path.exists(p):
            # Map specific library folders to the expected data directory names
            for sub, dest in [("tcl8.6", "_tcl_data"), ("tk8.6", "_tk_data")]:
                sub_path = os.path.join(p, sub)
                if os.path.exists(sub_path):
                    add_data.append((sub_path, dest))
                    tcl_found = True
            if tcl_found:
                print(f"Found Tcl/Tk data at: {p}")
                break
    
    # MANUAL BUNDLING OF TKINTER MODULE
    # Force include the python side of tkinter from the base library
    tk_lib_path = os.path.join(sys.base_prefix, "Lib", "tkinter")
    if os.path.exists(tk_lib_path):
        print(f"Manually bundling tkinter library from: {tk_lib_path}")
        add_data.append((tk_lib_path, "tkinter"))
    
    # Force include the _tkinter.pyd extension
    tk_pyd_path = os.path.join(sys.base_prefix, "DLLs", "_tkinter.pyd")
    if os.path.exists(tk_pyd_path):
        print(f"Manually bundling _tkinter.pyd from: {tk_pyd_path}")
        add_data.append((tk_pyd_path, "."))
    
    # Icon path
    icon_path = os.path.join("app", "static", "img", "logo.png")
    
    if not os.path.exists(icon_path):
        # Fallback to .ico if logo.png is not compatible directly or missing
        icon_path = None

    args = [
        entry_point,
        "--name", app_name,
        "--windowed", # No console window
        "--onefile", # Single executable
        "--clean",
        "--paths", os.path.join(sys.base_prefix, "Lib"), # Help find stdlib from base python
    ]
    
    for src, dest in add_data:
        args.extend(["--add-data", f"{src}{separator}{dest}"])
        
    if icon_path:
        args.extend(["--icon", icon_path])
        
    # Hidden imports that might be missed
    hidden_imports = [
        "flask",
        "flask_sqlalchemy",
        "flask_login",
        "flask_migrate",
        "clr-loader", # For pywebview on Windows
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "_tkinter", # Explicitly include the C extension
        "certifi",
    ]
    
    for imp in hidden_imports:
        args.extend(["--hidden-import", imp])
        
    # Aggressive bundling for tkinter
    args.extend(["--collect-all", "tkinter"])
    args.extend(["--collect-submodules", "tkinter"])

    print(f"Building {app_name}...")
    PyInstaller.__main__.run(args)
    print(f"Build complete. Check the 'dist' folder.")

if __name__ == "__main__":
    build()
