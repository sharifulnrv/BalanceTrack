import tkinter
import os
import sys

try:
    root = tkinter.Tk()
    tcl_lib = root.tk.exprstring('info library')
    tk_lib = root.tk.exprstring('set tk_library')
    print(f"TCL_LIB={tcl_lib}")
    print(f"TK_LIB={tk_lib}")
    root.destroy()
except Exception as e:
    print(f"ERROR: {e}")
