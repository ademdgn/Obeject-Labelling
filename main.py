import tkinter as tk
from tkinter import ttk
import sys
import os

from gui.main_window import MainWindow

def main():
    """Ana uygulama fonksiyonu"""
    # Tkinter uygulamasını başlat
    root = tk.Tk()
    
    # Uygulama simgesi (eğer varsa)
    try:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except Exception:
        pass
    
    # Uygulama başlığı
    root.title("Görsel Etiketleme Aracı")
    
    # Pencere boyutu
    root.geometry("1200x800")
    
    # Ana pencereyi oluştur
    app = MainWindow(root)
    
    # Uygulamayı başlat
    root.mainloop()

if __name__ == "__main__":
    main() 