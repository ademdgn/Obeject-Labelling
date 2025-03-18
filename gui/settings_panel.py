import tkinter as tk
from tkinter import ttk, colorchooser

class SettingsPanel:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        # Ana frame
        self.frame = ttk.LabelFrame(parent, text="Ayarlar")
        self.frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Izgara ayarları
        self.create_grid_settings()
        
        # Yakınlaştırma ayarları
        self.create_zoom_settings()
        
        # Otomatik kaydetme ayarları
        self.create_autosave_settings()
        
        # Sayfa boyutu ayarları
        self.create_page_size_settings()
        
        # Renk ayarları
        self.create_color_settings()
    
    def create_grid_settings(self):
        """Izgara ayarlarını oluştur"""
        grid_frame = ttk.LabelFrame(self.frame, text="Izgara")
        grid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Izgara etkinleştirme
        self.grid_enabled_var = tk.BooleanVar(value=self.main_window.grid_enabled)
        ttk.Checkbutton(grid_frame, text="Izgarayı Göster", 
                       variable=self.grid_enabled_var,
                       command=self.main_window.on_toggle_grid).pack(fill=tk.X, padx=5, pady=2)
        
        # Izgara boyutu
        size_frame = ttk.Frame(grid_frame)
        size_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(size_frame, text="Izgara Boyutu:").pack(side=tk.LEFT)
        
        self.grid_size_var = tk.StringVar(value=str(self.main_window.grid_size))
        grid_size_entry = ttk.Entry(size_frame, textvariable=self.grid_size_var, width=5)
        grid_size_entry.pack(side=tk.LEFT, padx=5)
        grid_size_entry.bind("<Return>", self.main_window.update_grid_size)
        
        ttk.Button(size_frame, text="Uygula", 
                  command=self.main_window.update_grid_size).pack(side=tk.LEFT)
    
    def create_zoom_settings(self):
        """Yakınlaştırma ayarlarını oluştur"""
        zoom_frame = ttk.LabelFrame(self.frame, text="Yakınlaştırma")
        zoom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Yakınlaştırma bilgisi
        self.zoom_label = ttk.Label(zoom_frame, text=f"Yakınlaştırma: {self.main_window.zoom_factor:.1f}x")
        self.zoom_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Yakınlaştırma butonları
        button_frame = ttk.Frame(zoom_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(button_frame, text="Yakınlaştır (+)", 
                  command=self.main_window.on_zoom_in).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(button_frame, text="Uzaklaştır (-)", 
                  command=self.main_window.on_zoom_out).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(button_frame, text="Sıfırla (1x)", 
                  command=self.main_window.on_zoom_reset).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def create_autosave_settings(self):
        """Otomatik kaydetme ayarlarını oluştur"""
        autosave_frame = ttk.LabelFrame(self.frame, text="Otomatik Kaydetme")
        autosave_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Otomatik kaydetme etkinleştirme
        self.autosave_enabled_var = tk.BooleanVar(value=self.main_window.autosave_enabled)
        ttk.Checkbutton(autosave_frame, text="Otomatik Kaydet", 
                       variable=self.autosave_enabled_var,
                       command=self.main_window.toggle_autosave).pack(fill=tk.X, padx=5, pady=2)
        
        # Otomatik kaydetme aralığı
        interval_frame = ttk.Frame(autosave_frame)
        interval_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(interval_frame, text="Aralık (sn):").pack(side=tk.LEFT)
        
        self.autosave_interval_var = tk.StringVar(value=str(self.main_window.autosave_interval // 1000))
        interval_entry = ttk.Entry(interval_frame, textvariable=self.autosave_interval_var, width=5)
        interval_entry.pack(side=tk.LEFT, padx=5)
        interval_entry.bind("<Return>", self.main_window.update_autosave_interval)
        
        ttk.Button(interval_frame, text="Uygula", 
                  command=self.main_window.update_autosave_interval).pack(side=tk.LEFT)
    
    def create_page_size_settings(self):
        """Sayfa boyutu ayarlarını oluştur"""
        page_frame = ttk.LabelFrame(self.frame, text="Sayfa Boyutu")
        page_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Sayfa boyutu açıklaması
        ttk.Label(page_frame, text="Page Up/Down tuşları için sayfa boyutu:").pack(fill=tk.X, padx=5, pady=2)
        
        # Sayfa boyutu seçimi
        self.page_size_var = tk.IntVar(value=10)  # Varsayılan değer
        
        size_frame = ttk.Frame(page_frame)
        size_frame.pack(fill=tk.X, padx=5, pady=2)
        
        for size in [5, 10, 20, 50]:
            ttk.Radiobutton(size_frame, text=str(size), variable=self.page_size_var, value=size).pack(side=tk.LEFT, padx=5)
    
    def create_color_settings(self):
        """Renk ayarlarını oluştur"""
        color_frame = ttk.LabelFrame(self.frame, text="Renkler")
        color_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(color_frame, text="Etiket Renklerini Ayarla", 
                  command=self.main_window.configure_label_colors).pack(fill=tk.X, padx=5, pady=2)
    
    def update_grid_settings(self, enabled, size):
        """Izgara ayarlarını güncelle"""
        self.grid_enabled_var.set(enabled)
        self.grid_size_var.set(str(size))
    
    def update_zoom_label(self, zoom_factor):
        """Yakınlaştırma etiketini güncelle"""
        self.zoom_label.config(text=f"Yakınlaştırma: {zoom_factor:.1f}x")
    
    def update_autosave_settings(self, enabled, interval):
        """Otomatik kaydetme ayarlarını güncelle"""
        self.autosave_enabled_var.set(enabled)
        self.autosave_interval_var.set(str(interval // 1000))  # Milisaniyeden saniyeye çevir 