import tkinter as tk
from tkinter import ttk

class MenuBar:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        
        # Menü çubuğu
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)
        
        # Dosya menüsü
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Dosya", menu=self.file_menu)
        
        self.file_menu.add_command(label="Fotoğraf Yükle", command=self.main_window.load_images)
        self.file_menu.add_command(label="Video Yükle", command=self.main_window.load_video)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Oturumdan Devam Et", command=self.main_window.resume_from_last_session)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Etiketleri Kaydet", command=self.main_window.save_annotations)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Çıkış", command=self.main_window.on_closing)
        
        # Frameler menüsü
        self.frames_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Frameler", menu=self.frames_menu)
        
        self.frames_menu.add_command(label="Frameleri Çıkar", command=self.main_window.extract_frames)
        self.frames_menu.add_separator()
        self.frames_menu.add_command(label="Önceki Frame", command=self.main_window.prev_frame)
        self.frames_menu.add_command(label="Sonraki Frame", command=self.main_window.next_frame)
        self.frames_menu.add_command(label="Frame'e Git", command=self.main_window.goto_specific_frame_dialog)
        self.frames_menu.add_separator()
        self.frames_menu.add_command(label="Önceki Sayfa", command=self.main_window.prev_page)
        self.frames_menu.add_command(label="Sonraki Sayfa", command=self.main_window.next_page)
        
        # Etiketler menüsü
        self.labels_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Etiketler", menu=self.labels_menu)
        
        self.labels_menu.add_command(label="Etiket Ekle", command=self.main_window.add_label)
        self.labels_menu.add_command(label="Etiket Renklerini Ayarla", command=self.main_window.configure_label_colors)
        self.labels_menu.add_separator()
        self.labels_menu.add_command(label="Tüm Kutuları Seç", command=self.main_window.select_all_boxes)
        self.labels_menu.add_command(label="Seçimi Kaldır", command=self.main_window.deselect_all)
        self.labels_menu.add_separator()
        self.labels_menu.add_command(label="Seçili Kutuları Sil", command=self.main_window.delete_selected_box)
        
        # Görünüm menüsü
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Görünüm", menu=self.view_menu)
        
        self.view_menu.add_command(label="Izgara Aç/Kapat", command=self.main_window.on_toggle_grid)
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Yakınlaştır", command=self.main_window.on_zoom_in)
        self.view_menu.add_command(label="Uzaklaştır", command=self.main_window.on_zoom_out)
        self.view_menu.add_command(label="Yakınlaştırmayı Sıfırla", command=self.main_window.on_zoom_reset)
        
        # Ayarlar menüsü
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Ayarlar", menu=self.settings_menu)
        
        self.settings_menu.add_command(label="Otomatik Kaydetme Ayarları", command=self.main_window.configure_autosave)
        self.settings_menu.add_command(label="Klavye Kısayollarını Yapılandır", command=self.main_window.configure_keyboard_shortcuts)
        
        # Yardım menüsü
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Yardım", menu=self.help_menu)
        
        self.help_menu.add_command(label="Kısayollar", command=self.show_shortcuts)
        self.help_menu.add_command(label="Hakkında", command=self.show_about)
    
    def show_shortcuts(self):
        """Kısayollar penceresini göster"""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Klavye Kısayolları")
        shortcuts_window.geometry("400x500")
        shortcuts_window.resizable(False, False)
        
        # Stil
        style = ttk.Style()
        style.configure("Shortcuts.TLabel", font=("Segoe UI", 9))
        
        # Ana frame
        main_frame = ttk.Frame(shortcuts_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        ttk.Label(main_frame, text="Klavye Kısayolları", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Kısayollar listesi
        shortcuts_frame = ttk.Frame(main_frame)
        shortcuts_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        shortcuts = [
            ("Navigasyon", ""),
            ("Sol Ok", "Önceki frame"),
            ("Sağ Ok", "Sonraki frame"),
            ("Page Up", "Önceki sayfa"),
            ("Page Down", "Sonraki sayfa"),
            ("Ctrl+F", "Frame'e git"),
            ("", ""),
            ("Etiketleme", ""),
            ("Tıklama ve Sürükleme", "Yeni kutu çiz"),
            ("Shift+Tıklama ve Sürükleme", "Kutuyu taşı"),
            ("Ctrl+Tıklama", "Çoklu seçim"),
            ("Delete", "Seçili kutuları sil"),
            ("Ctrl+A", "Tüm kutuları seç"),
            ("Escape", "Seçimi kaldır"),
            ("", ""),
            ("Düzenleme", ""),
            ("Ctrl+S", "Etiketleri kaydet"),
            ("Ctrl+Z", "Son işlemi geri al"),
            ("Ctrl+Y", "Son işlemi yeniden yap"),
            ("", ""),
            ("Görünüm", ""),
            ("Ctrl+G", "Izgara aç/kapat"),
            ("Ctrl++", "Yakınlaştır"),
            ("Ctrl+-", "Uzaklaştır"),
            ("Ctrl+0", "Yakınlaştırmayı sıfırla")
        ]
        
        for i, (key, desc) in enumerate(shortcuts):
            frame = ttk.Frame(shortcuts_frame)
            frame.pack(fill=tk.X, pady=2)
            
            if not key and not desc:
                # Boş satır
                ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
                continue
            
            if desc == "":
                # Kategori başlığı
                ttk.Label(frame, text=key, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=5)
                continue
            
            ttk.Label(frame, text=key, width=25, style="Shortcuts.TLabel").pack(side=tk.LEFT, anchor=tk.W)
            ttk.Label(frame, text=desc, style="Shortcuts.TLabel").pack(side=tk.LEFT, anchor=tk.W)
        
        # Kapat butonu
        ttk.Button(main_frame, text="Kapat", command=shortcuts_window.destroy).pack(pady=10)
    
    def show_about(self):
        """Hakkında penceresini göster"""
        about_window = tk.Toplevel(self.root)
        about_window.title("Hakkında")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        # Ana frame
        main_frame = ttk.Frame(about_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        ttk.Label(main_frame, text="Görsel Etiketleme Aracı", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        # Versiyon
        ttk.Label(main_frame, text="Versiyon 1.0").pack()
        
        # Açıklama
        description = """
        Bu uygulama, görüntü ve video dosyalarını etiketlemek için tasarlanmış 
        kullanıcı dostu bir araçtır. YOLO formatında etiketler oluşturarak 
        nesne tanıma modelleri için veri seti hazırlamanıza yardımcı olur.
        """
        
        ttk.Label(main_frame, text=description, wraplength=350, justify=tk.CENTER).pack(pady=20)
        
        # Telif hakkı
        ttk.Label(main_frame, text="© 2023 Tüm hakları saklıdır.").pack(pady=10)
        
        # Kapat butonu
        ttk.Button(main_frame, text="Kapat", command=about_window.destroy).pack(pady=10) 