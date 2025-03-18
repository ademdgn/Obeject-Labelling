import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import os
import cv2
import numpy as np
from PIL import Image, ImageTk
import json

from gui.menu_bar import MenuBar
from gui.settings_panel import SettingsPanel
from gui.annotation_panel import AnnotationPanel
from utils.file_utils import (create_output_dirs, save_session_info, load_session_info,
                             extract_frames_from_video, load_frames_from_dir,
                             save_annotations, load_annotations)
from utils.image_utils import (resize_frame, create_photo_image, draw_grid,
                              canvas_to_image_coords, image_to_canvas_coords)
from utils.annotation_utils import (find_box_at_position, draw_boxes,
                                   move_box, resize_box)

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Görsel Etiketleme Aracı")
        self.root.geometry("1200x800")
        
        # Tema ayarları
        self.set_theme()
        
        # Uygulama durumu
        self.video_path = None
        self.output_dir = None
        self.frames = []
        self.current_frame_idx = 0
        self.labels = []
        self.current_boxes = []
        self.drawing = False
        self.moving = False
        self.selected_box_idx = -1
        self.start_x, self.start_y = 0, 0
        self.move_start_x, self.move_start_y = 0, 0
        self.session_file = "session_info.json"
        self.shortcuts_file = "keyboard_shortcuts.json"
        
        # Fare üzerinde olan kutu indeksi
        self.hover_box_idx = -1
        
        # Izgara modu ayarları
        self.grid_enabled = False
        self.grid_size = 50
        self.grid_color = "gray"
        
        # Yakınlaştırma ayarları
        self.zoom_factor = 1.0
        self.max_zoom = 5.0
        self.min_zoom = 0.5
        
        # Otomatik kaydetme ayarları
        self.autosave_enabled = False
        self.autosave_interval = 60000  # Milisaniye cinsinden (60 saniye)
        self.autosave_job = None
        
        # Etiket renkleri
        self.label_colors = {}
        
        # Çoklu seçim için değişkenler
        self.selected_box_indices = []
        self.last_action = None
        self.action_history = []
        
        # Klavye kısayolları için değişkenler
        self.keyboard_shortcuts = {
            "prev_frame": "<Left>",
            "next_frame": "<Right>",
            "save_annotations": "<Control-s>",
            "undo_last_action": "<Control-z>",
            "redo_last_action": "<Control-y>",
            "toggle_grid": "<Control-g>",
            "zoom_in": "<Control-plus>",
            "zoom_out": "<Control-minus>",
            "zoom_reset": "<Control-0>",
            "goto_frame": "<Control-f>",
            "select_all": "<Control-a>",
            "deselect_all": "<Escape>",
            "delete_box": "<Delete>",
            "prev_page": "<Prior>",
            "next_page": "<Next>"
        }
        
        # Klavye kısayollarını yükle
        self.load_keyboard_shortcuts()
        
        # Ana frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Menü çubuğu
        self.menu_bar = MenuBar(self.root, self)
        
        # Sol panel - Kontroller (scrollable)
        self.control_frame_outer = ttk.Frame(self.main_frame, width=300)
        self.control_frame_outer.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.control_frame_outer.pack_propagate(False)  # Boyutu sabit tut
        
        # Scrollbar ekle
        self.control_scrollbar = ttk.Scrollbar(self.control_frame_outer)
        self.control_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas ekle (scrollable içerik için)
        self.control_canvas = tk.Canvas(self.control_frame_outer, yscrollcommand=self.control_scrollbar.set)
        self.control_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.control_scrollbar.config(command=self.control_canvas.yview)
        
        # İç frame (gerçek içerik)
        self.control_frame = ttk.Frame(self.control_canvas)
        self.control_canvas_window = self.control_canvas.create_window((0, 0), window=self.control_frame, anchor=tk.NW)
        
        # Canvas boyutlandırma olayları
        self.control_frame.bind("<Configure>", self._on_control_frame_configure)
        self.control_canvas.bind("<Configure>", self._on_control_canvas_configure)
        
        # Fare tekerleği ile scroll
        self.control_canvas.bind("<MouseWheel>", self._on_control_mousewheel)  # Windows
        self.control_canvas.bind("<Button-4>", self._on_control_mousewheel)  # Linux yukarı kaydırma
        self.control_canvas.bind("<Button-5>", self._on_control_mousewheel)  # Linux aşağı kaydırma
        
        # Ayarlar paneli
        self.settings_panel = SettingsPanel(self.control_frame, self)
        
        # Anotasyon paneli
        self.annotation_panel = AnnotationPanel(self.control_frame, self)
        
        # Sağ panel - Görüntü
        self.image_frame = ttk.Frame(self.main_frame)
        self.image_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas
        self.canvas_frame = ttk.LabelFrame(self.image_frame, text="Görüntü")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#1e1e1e")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Durum çubuğu
        self.status_bar = ttk.Label(self.root, text="Hazır", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Canvas olayları
        self.setup_canvas_events()
        
        # Klavye kısayolları
        self.setup_keyboard_shortcuts()
        
        # Sağ tık menüsü
        self.create_context_menu()
        
        # Programdan çıkış yaparken oturum bilgilerini kaydet
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Otomatik kaydetme işlemini başlat
        if self.autosave_enabled:
            self.autosave_job = self.root.after(self.autosave_interval, self.autosave)
    
    def load_keyboard_shortcuts(self):
        """Klavye kısayollarını yükle"""
        # Kısayollar dosyası var mı kontrol et
        if os.path.exists(self.shortcuts_file):
            try:
                with open(self.shortcuts_file, 'r', encoding='utf-8') as f:
                    shortcuts = json.load(f)
                
                # Kısayolları güncelle
                for key, value in shortcuts.items():
                    if key in self.keyboard_shortcuts:
                        self.keyboard_shortcuts[key] = value
                
                print(f"Klavye kısayolları yüklendi: {self.shortcuts_file}")
            except Exception as e:
                print(f"Klavye kısayolları yüklenirken hata oluştu: {e}")
    
    def save_keyboard_shortcuts(self):
        """Klavye kısayollarını kaydet"""
        try:
            with open(self.shortcuts_file, 'w', encoding='utf-8') as f:
                json.dump(self.keyboard_shortcuts, f, indent=4)
            
            print(f"Klavye kısayolları kaydedildi: {self.shortcuts_file}")
            return True
        except Exception as e:
            print(f"Klavye kısayolları kaydedilirken hata oluştu: {e}")
            return False
    
    def save_shortcuts(self, shortcut_entries, window):
        """Kısayolları kaydet"""
        # Kısayolları yeniden ayarla
        self.setup_keyboard_shortcuts()
        
        # Kısayolları dosyaya kaydet
        if self.save_keyboard_shortcuts():
            # Kullanıcıya bilgi ver
            messagebox.showinfo("Bilgi", "Klavye kısayolları kaydedildi.")
        else:
            # Hata mesajı
            messagebox.showerror("Hata", "Klavye kısayolları kaydedilemedi.")
        
        # Pencereyi kapat
        window.destroy()
    
    def _on_control_frame_configure(self, event):
        """İç frame boyutu değiştiğinde scrollbar'ı güncelle"""
        self.control_canvas.configure(scrollregion=self.control_canvas.bbox("all"))
    
    def _on_control_canvas_configure(self, event):
        """Canvas boyutu değiştiğinde iç frame genişliğini güncelle"""
        self.control_canvas.itemconfig(self.control_canvas_window, width=event.width)
    
    def _on_control_mousewheel(self, event):
        """Fare tekerleği ile scroll"""
        # Windows için
        if event.num == 5 or event.delta < 0:
            self.control_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.control_canvas.yview_scroll(-1, "units")
    
    def set_theme(self):
        """Uygulama temasını ayarla"""
        style = ttk.Style()
        
        # Mevcut temayı kontrol et
        current_theme = style.theme_use()
        
        # Eğer 'clam' teması varsa kullan, yoksa mevcut temayı kullan
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
            # Tema renkleri
            style.configure('TFrame', background='#f0f0f0')
            style.configure('TLabel', background='#f0f0f0', foreground='#333333')
            style.configure('TButton', background='#4a7dfc', foreground='#ffffff')
            style.configure('TCheckbutton', background='#f0f0f0')
            style.configure('TRadiobutton', background='#f0f0f0')
            
            # LabelFrame için özel stil
            style.configure('TLabelframe', background='#f0f0f0')
            style.configure('TLabelframe.Label', background='#f0f0f0', foreground='#333333', font=('Arial', 9, 'bold'))
            
            # Entry için özel stil
            style.configure('TEntry', fieldbackground='#ffffff')
            
            # Combobox için özel stil
            style.configure('TCombobox', fieldbackground='#ffffff')
            
            # Scrollbar için özel stil
            style.configure('TScrollbar', background='#dddddd', troughcolor='#f0f0f0')
        
        # Yazı tipi ayarları
        default_font = ('Segoe UI', 9)
        self.root.option_add('*Font', default_font)
    
    def setup_canvas_events(self):
        """Canvas için olay dinleyicilerini ayarla"""
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<ButtonPress-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_mouse_hover)  # Fare hareketi izleme
        
        # Fare tekerleği ile yakınlaştırma/uzaklaştırma
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux yukarı kaydırma
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux aşağı kaydırma
        
        # Shift ile taşıma
        self.root.bind("<Shift-ButtonPress-1>", self.on_shift_mouse_down)
        self.root.bind("<Shift-B1-Motion>", self.on_shift_mouse_move)
        self.root.bind("<Shift-ButtonRelease-1>", self.on_shift_mouse_up)
    
    def setup_keyboard_shortcuts(self):
        """Klavye kısayollarını ayarla"""
        # Tüm kısayolları temizle
        for shortcut in self.keyboard_shortcuts.values():
            self.root.unbind(shortcut)
        
        # Kısayolları yeniden bağla
        self.root.bind(self.keyboard_shortcuts["prev_frame"], self.on_prev_frame)
        self.root.bind(self.keyboard_shortcuts["next_frame"], self.on_next_frame)
        self.root.bind(self.keyboard_shortcuts["save_annotations"], self.on_save_annotations)
        self.root.bind(self.keyboard_shortcuts["undo_last_action"], self.on_undo_last_action)
        self.root.bind(self.keyboard_shortcuts["redo_last_action"], self.on_redo_last_action)
        self.root.bind(self.keyboard_shortcuts["toggle_grid"], self.on_toggle_grid)
        self.root.bind(self.keyboard_shortcuts["zoom_in"], self.on_zoom_in)
        self.root.bind(self.keyboard_shortcuts["zoom_out"], self.on_zoom_out)
        self.root.bind(self.keyboard_shortcuts["zoom_reset"], self.on_zoom_reset)
        self.root.bind(self.keyboard_shortcuts["goto_frame"], self.on_goto_frame)
        self.root.bind(self.keyboard_shortcuts["select_all"], self.on_select_all)
        self.root.bind(self.keyboard_shortcuts["deselect_all"], self.on_deselect_all)
        self.root.bind(self.keyboard_shortcuts["delete_box"], self.on_delete_box)
        self.root.bind(self.keyboard_shortcuts["prev_page"], self.on_prev_page)
        self.root.bind(self.keyboard_shortcuts["next_page"], self.on_next_page)
    
    # Klavye kısayolları için olay işleyicileri
    def on_prev_frame(self, event=None):
        """Önceki frame'e git"""
        self.prev_frame()
    
    def on_next_frame(self, event=None):
        """Sonraki frame'e git"""
        self.next_frame()
    
    def on_save_annotations(self, event=None):
        self.save_annotations()
    
    def on_undo_last_action(self, event=None):
        """Son işlemi geri al (Ctrl+Z)"""
        if not self.action_history:
            return
        
        # undone_actions listesini oluştur (yoksa)
        if not hasattr(self, 'undone_actions'):
            self.undone_actions = []
        
        # Son işlemi al
        action, boxes, selected = self.action_history.pop()
        
        # Geri alınan işlemi undone_actions listesine ekle
        self.undone_actions.append(("undo", self.current_boxes.copy(), self.selected_box_indices.copy()))
        
        # İşlemi geri al
        self.current_boxes = boxes
        self.selected_box_indices = selected
        
        # Kutuları yeniden çiz
        self.show_current_frame()
        
        # Etiketleri hemen kaydet
        if self.frames:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir, silent=True)
            if save_result:
                self.status_bar.config(text="Son işlem geri alındı.")
            else:
                self.status_bar.config(text="Etiketler kaydedilemedi (geri alma sonrası).")
    
    def on_redo_last_action(self, event=None):
        """Son geri alınan işlemi yeniden yap (Ctrl+Y)"""
        # Henüz uygulanmadı
        if not hasattr(self, 'undone_actions'):
            self.undone_actions = []
        
        if not self.undone_actions:
            self.status_bar.config(text="Yeniden yapılacak işlem yok.")
            return
        
        # Son geri alınan işlemi al
        action, boxes, selected = self.undone_actions.pop()
        
        # İşlemi yeniden yap
        self.action_history.append((action, self.current_boxes.copy(), self.selected_box_indices.copy()))
        self.current_boxes = boxes
        self.selected_box_indices = selected
        
        # Kutuları yeniden çiz
        self.show_current_frame()
        
        # Etiketleri hemen kaydet
        if self.frames:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir, silent=True)
            if save_result:
                self.status_bar.config(text="Son işlem yeniden yapıldı.")
            else:
                self.status_bar.config(text="Etiketler kaydedilemedi.")
    
    def on_toggle_grid(self, event=None):
        """Izgara görünümünü aç/kapat"""
        self.grid_enabled = not self.grid_enabled
        self.show_current_frame()
        
        # Durum çubuğunu güncelle
        if self.grid_enabled:
            self.status_bar.config(text="Izgara görünümü açıldı")
        else:
            self.status_bar.config(text="Izgara görünümü kapatıldı")
    
    def on_zoom_in(self, event=None):
        """Görüntüyü yakınlaştır"""
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor += 0.1
            self.show_current_frame()
            self.status_bar.config(text=f"Yakınlaştırma: {self.zoom_factor:.1f}x")
    
    def on_zoom_out(self, event=None):
        """Görüntüyü uzaklaştır"""
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor -= 0.1
            self.show_current_frame()
            self.status_bar.config(text=f"Uzaklaştırma: {self.zoom_factor:.1f}x")
    
    def on_zoom_reset(self, event=None):
        """Yakınlaştırmayı sıfırla"""
        self.zoom_factor = 1.0
        self.show_current_frame()
        self.status_bar.config(text="Yakınlaştırma sıfırlandı")
    
    def on_goto_frame(self, event=None):
        self.goto_specific_frame_dialog()
    
    def on_select_all(self, event=None):
        self.select_all_boxes()
    
    def on_deselect_all(self, event=None):
        self.deselect_all()
    
    def on_delete_box(self, event=None):
        self.delete_box_or_selected()
    
    def on_prev_page(self, event=None):
        self.prev_page()
    
    def on_next_page(self, event=None):
        self.next_page()
    
    def configure_keyboard_shortcuts(self):
        """Klavye kısayollarını yapılandır"""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Klavye Kısayollarını Yapılandır")
        shortcuts_window.geometry("500x600")
        shortcuts_window.resizable(True, True)
        
        # Ana frame
        main_frame = ttk.Frame(shortcuts_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        ttk.Label(main_frame, text="Klavye Kısayollarını Yapılandır", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Açıklama
        ttk.Label(main_frame, text="Aşağıdaki işlemler için klavye kısayollarını özelleştirebilirsiniz.", 
                 wraplength=480, justify=tk.CENTER).pack(pady=5)
        
        # Scrollable frame
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(canvas_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas
        canvas = tk.Canvas(canvas_frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=canvas.yview)
        
        # İç frame
        inner_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)
        
        # Kısayol açıklamaları
        shortcut_descriptions = {
            "prev_frame": "Önceki Frame",
            "next_frame": "Sonraki Frame",
            "save_annotations": "Etiketleri Kaydet",
            "undo_last_action": "Son İşlemi Geri Al",
            "redo_last_action": "Son İşlemi Yeniden Yap",
            "toggle_grid": "Izgara Aç/Kapat",
            "zoom_in": "Yakınlaştır",
            "zoom_out": "Uzaklaştır",
            "zoom_reset": "Yakınlaştırmayı Sıfırla",
            "goto_frame": "Frame'e Git",
            "select_all": "Tümünü Seç",
            "deselect_all": "Seçimi Kaldır",
            "delete_box": "Seçili Kutuyu Sil",
            "prev_page": "Önceki Sayfa",
            "next_page": "Sonraki Sayfa"
        }
        
        # Tuş seçenekleri
        key_options = [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "Left", "Right", "Up", "Down", "Home", "End", "Page_Up", "Page_Down",
            "Insert", "Delete", "Escape", "Tab", "space", "Return", "BackSpace",
            "plus", "minus", "equal", "comma", "period", "slash", "backslash"
        ]
        
        # Kısayol giriş alanları
        shortcut_entries = {}
        
        # Başlık satırı
        header_frame = ttk.Frame(inner_frame)
        header_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(header_frame, text="İşlem", width=25, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Tuş", width=15, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Modifier", width=20, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Ayırıcı
        ttk.Separator(inner_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Kısayolları listele
        for shortcut_id, description in shortcut_descriptions.items():
            frame = ttk.Frame(inner_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=description, width=25).pack(side=tk.LEFT, padx=5)
            
            # Mevcut kısayol bilgisi
            current_shortcut = self.keyboard_shortcuts[shortcut_id].replace("<", "").replace(">", "")
            key = current_shortcut
            modifiers = []
            
            if "-" in current_shortcut:
                parts = current_shortcut.split("-")
                key = parts[-1]
                for i in range(len(parts) - 1):
                    if parts[i] == "Control":
                        modifiers.append("Ctrl")
                    elif parts[i] == "Alt":
                        modifiers.append("Alt")
                    elif parts[i] == "Shift":
                        modifiers.append("Shift")
            
            # Tuş seçimi
            key_var = tk.StringVar(value=key)
            key_dropdown = ttk.Combobox(frame, textvariable=key_var, values=key_options, width=15)
            key_dropdown.pack(side=tk.LEFT, padx=5)
            
            # Modifier seçimi
            modifier_frame = ttk.Frame(frame)
            modifier_frame.pack(side=tk.LEFT, padx=5)
            
            ctrl_var = tk.BooleanVar(value="Ctrl" in modifiers)
            alt_var = tk.BooleanVar(value="Alt" in modifiers)
            shift_var = tk.BooleanVar(value="Shift" in modifiers)
            
            ttk.Checkbutton(modifier_frame, text="Ctrl", variable=ctrl_var).pack(side=tk.LEFT)
            ttk.Checkbutton(modifier_frame, text="Alt", variable=alt_var).pack(side=tk.LEFT)
            ttk.Checkbutton(modifier_frame, text="Shift", variable=shift_var).pack(side=tk.LEFT)
            
            shortcut_entries[shortcut_id] = (key_var, ctrl_var, alt_var, shift_var)
        
        # Canvas boyutlandırma olayları
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def update_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        inner_frame.bind("<Configure>", update_scrollregion)
        canvas.bind("<Configure>", update_canvas_width)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def reset_shortcuts():
            self.reset_shortcuts_to_default_new(shortcut_entries)
        
        def save_shortcuts():
            self.save_shortcuts_new(shortcut_entries, shortcuts_window)
        
        ttk.Button(button_frame, text="Varsayılana Sıfırla", 
                  command=reset_shortcuts).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Kaydet", 
                  command=save_shortcuts).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="İptal", 
                  command=shortcuts_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def reset_shortcuts_to_default_new(self, shortcut_entries):
        """Kısayolları varsayılana sıfırla (yeni)"""
        default_shortcuts = {
            "prev_frame": "<Left>",
            "next_frame": "<Right>",
            "save_annotations": "<Control-s>",
            "undo_last_action": "<Control-z>",
            "redo_last_action": "<Control-y>",
            "toggle_grid": "<Control-g>",
            "zoom_in": "<Control-plus>",
            "zoom_out": "<Control-minus>",
            "zoom_reset": "<Control-0>",
            "goto_frame": "<Control-f>",
            "select_all": "<Control-a>",
            "deselect_all": "<Escape>",
            "delete_box": "<Delete>",
            "prev_page": "<Prior>",
            "next_page": "<Next>"
        }
        
        # Kısayolları sıfırla
        self.keyboard_shortcuts = default_shortcuts.copy()
        
        # Görüntülenen kısayolları güncelle
        for shortcut_id, (key_var, ctrl_var, alt_var, shift_var) in shortcut_entries.items():
            current_shortcut = default_shortcuts[shortcut_id].replace("<", "").replace(">", "")
            key = current_shortcut
            
            # Modifier'ları sıfırla
            ctrl_var.set(False)
            alt_var.set(False)
            shift_var.set(False)
            
            if "-" in current_shortcut:
                parts = current_shortcut.split("-")
                key = parts[-1]
                for i in range(len(parts) - 1):
                    if parts[i] == "Control":
                        ctrl_var.set(True)
                    elif parts[i] == "Alt":
                        alt_var.set(True)
                    elif parts[i] == "Shift":
                        shift_var.set(True)
            
            key_var.set(key)
    
    def save_shortcuts_new(self, shortcut_entries, window):
        """Kısayolları kaydet (yeni)"""
        # Kısayolları güncelle
        for shortcut_id, (key_var, ctrl_var, alt_var, shift_var) in shortcut_entries.items():
            key = key_var.get()
            
            # Özel tuşlar için düzeltmeler
            if key.lower() == "page_up":
                key = "Prior"
            elif key.lower() == "page_down":
                key = "Next"
            
            # Tkinter formatına dönüştür
            tk_shortcut = "<"
            if ctrl_var.get():
                tk_shortcut += "Control-"
            if alt_var.get():
                tk_shortcut += "Alt-"
            if shift_var.get():
                tk_shortcut += "Shift-"
            tk_shortcut += key + ">"
            
            # Kısayolu güncelle
            self.keyboard_shortcuts[shortcut_id] = tk_shortcut
        
        # Kısayolları yeniden ayarla
        try:
            self.setup_keyboard_shortcuts()
        except Exception as e:
            messagebox.showerror("Hata", f"Kısayollar ayarlanırken bir hata oluştu: {e}")
            return
        
        # Kısayolları dosyaya kaydet
        if self.save_keyboard_shortcuts():
            # Kullanıcıya bilgi ver
            messagebox.showinfo("Bilgi", "Klavye kısayolları kaydedildi.")
        else:
            # Hata mesajı
            messagebox.showerror("Hata", "Klavye kısayolları kaydedilemedi.")
        
        # Pencereyi kapat
        window.destroy()
    
    def on_mouse_down(self, event):
        """Sol tıklama olayı"""
        if not self.frames:
            return
        
        # Canvas boyutlarını al
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Mevcut frame'i al
        frame_data, frame_path = self.frames[self.current_frame_idx]
        img_h, img_w = frame_data.shape[:2]
        
        # Canvas koordinatlarını görüntü koordinatlarına dönüştür
        img_x, img_y = canvas_to_image_coords(event.x, event.y, img_w, img_h, 
                                             canvas_width, canvas_height, self.zoom_factor)
        
        # Ctrl tuşuna basılıysa, çoklu seçim modunda
        if event.state & 0x4:  # Ctrl tuşu
            # Tıklanan konumda bir kutu var mı kontrol et
            box_idx = find_box_at_position(img_x, img_y, self.current_boxes)
            
            if box_idx >= 0:
                # Kutu zaten seçiliyse, seçimi kaldır
                if box_idx in self.selected_box_indices:
                    self.selected_box_indices.remove(box_idx)
                # Değilse, seçime ekle
                else:
                    self.selected_box_indices.append(box_idx)
                
                # Kutuları yeniden çiz
                self.show_current_frame()
            return
        
        # Tıklanan konumda bir kutu var mı kontrol et
        box_idx = find_box_at_position(img_x, img_y, self.current_boxes)
        
        if box_idx >= 0:
            # Kutuyu seç
            self.selected_box_indices = [box_idx]
            self.selected_box_idx = box_idx
            
            # Kutuları yeniden çiz
            self.show_current_frame()
        else:
            # Yeni kutu çizmeye başla
            current_label = self.annotation_panel.current_label_var.get()
            
            # Etiket kontrolü
            if not self.labels:
                messagebox.showinfo("Bilgi", "Önce etiket eklemelisiniz. 'Etiket Ekle' butonuna tıklayın.")
                return
            
            if current_label == "Etiket seçin" or current_label not in self.labels:
                if self.labels:
                    # Varsayılan olarak ilk etiketi seç
                    self.annotation_panel.current_label_var.set(self.labels[0])
                    current_label = self.labels[0]
                    messagebox.showinfo("Bilgi", f"Varsayılan etiket seçildi: {current_label}")
                else:
                    messagebox.showinfo("Bilgi", "Önce etiket eklemelisiniz. 'Etiket Ekle' butonuna tıklayın.")
                    return
            
            self.drawing = True
            self.start_x, self.start_y = img_x, img_y
            
            # Hover durumunu sıfırla
            self.hover_box_idx = -1
            
            # Seçili kutuları temizle
            self.selected_box_indices = []
    
    def on_mouse_move(self, event):
        """Fare hareketi olayı"""
        if not self.frames:
            return
            
        # Canvas boyutlarını al
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Mevcut frame'i al
        frame_data, frame_path = self.frames[self.current_frame_idx]
        img_h, img_w = frame_data.shape[:2]
        
        # Canvas koordinatlarını görüntü koordinatlarına dönüştür
        img_x, img_y = canvas_to_image_coords(event.x, event.y, img_w, img_h, 
                                             canvas_width, canvas_height, self.zoom_factor)
        
        # Fare bir kutunun üzerinde mi kontrol et
        if not self.drawing:
            box_idx = find_box_at_position(img_x, img_y, self.current_boxes)
            
            if box_idx != self.hover_box_idx:
                self.hover_box_idx = box_idx
                self.show_current_frame()
                
                if box_idx >= 0:
                    x1, y1, x2, y2, label = self.current_boxes[box_idx]
                    width = x2 - x1
                    height = y2 - y1
                    self.status_bar.config(text=f"Kutu: ({x1}, {y1}) - ({x2}, {y2}) | Boyut: {width}x{height} | Etiket: {label}")
                else:
                    self.status_bar.config(text=f"Fare: ({img_x}, {img_y})")
        
        # Çizim modunda
        if self.drawing:
            # Geçici kutuyu çiz
            self.show_current_frame()  # Önce mevcut frame'i temizle
            
            # Görüntü koordinatlarını canvas koordinatlarına dönüştür
            x1_canvas, y1_canvas = image_to_canvas_coords(self.start_x, self.start_y, img_w, img_h, 
                                                        canvas_width, canvas_height, self.zoom_factor)
            x2_canvas, y2_canvas = image_to_canvas_coords(img_x, img_y, img_w, img_h, 
                                                        canvas_width, canvas_height, self.zoom_factor)
            
            # Geçici kutuyu çiz
            self.canvas.create_rectangle(
                x1_canvas, y1_canvas, x2_canvas, y2_canvas,
                outline="yellow", width=2, tags="temp_box"
            )
            
            # Durum çubuğunu güncelle
            width = abs(img_x - self.start_x)
            height = abs(img_y - self.start_y)
            self.status_bar.config(text=f"Çizim: ({self.start_x}, {self.start_y}) - ({img_x}, {img_y}) | Boyut: {width}x{height}")
    
    def on_mouse_up(self, event):
        """Sol tıklama bırakma olayı"""
        if not self.frames or not self.drawing:
            return
        
        self.drawing = False
        
        # Canvas boyutlarını al
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Mevcut frame'i al
        frame_data, frame_path = self.frames[self.current_frame_idx]
        img_h, img_w = frame_data.shape[:2]
        
        # Canvas koordinatlarını görüntü koordinatlarına dönüştür
        img_x, img_y = canvas_to_image_coords(event.x, event.y, img_w, img_h, 
                                             canvas_width, canvas_height, self.zoom_factor)
        
        # Kutu boyutlarını hesapla
        x1 = min(self.start_x, img_x)
        y1 = min(self.start_y, img_y)
        x2 = max(self.start_x, img_x)
        y2 = max(self.start_y, img_y)
        
        # Kutu çok küçükse, oluşturma
        if x2 - x1 < 5 or y2 - y1 < 5:
            self.show_current_frame()
            return
        
        # Kutuyu sınırlar içinde tut
        x1 = max(0, min(x1, img_w - 1))
        y1 = max(0, min(y1, img_h - 1))
        x2 = max(0, min(x2, img_w - 1))
        y2 = max(0, min(y2, img_h - 1))
        
        # Etiket seç
        label = self.annotation_panel.current_label_var.get()
        
        # Etiket kontrolü
        if label == "Etiket seçin" or label not in self.labels:
            if self.labels:
                # Varsayılan olarak ilk etiketi seç
                label = self.labels[0]
                self.annotation_panel.current_label_var.set(label)
                messagebox.showinfo("Bilgi", f"Varsayılan etiket seçildi: {label}")
            else:
                messagebox.showinfo("Bilgi", "Önce etiket eklemelisiniz. 'Etiket Ekle' butonuna tıklayın.")
                self.show_current_frame()
                return
        
        # Yeni kutuyu ekle
        new_box = (x1, y1, x2, y2, label)
        self.current_boxes.append(new_box)
        
        # İşlem geçmişine ekle (geri alma için)
        self.action_history.append(("add", 
                                   [b for b in self.current_boxes if b != new_box], 
                                   self.selected_box_indices.copy()))
        
        # undone_actions listesini temizle (yeni bir işlem yapıldığında)
        if hasattr(self, 'undone_actions'):
            self.undone_actions = []
        
        # Yeni kutuyu seç
        self.selected_box_indices = [len(self.current_boxes) - 1]
        
        # Kutuları yeniden çiz
        self.show_current_frame()
        
        # Durum çubuğunu güncelle
        width = x2 - x1
        height = y2 - y1
        self.status_bar.config(text=f"Kutu eklendi: ({x1}, {y1}) - ({x2}, {y2}) | Boyut: {width}x{height}")
        
        # Etiketleri hemen kaydet
        if self.frames:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir, silent=True)
            if not save_result:
                self.status_bar.config(text="Etiketler kaydedilemedi.")
    
    def on_right_click(self, event):
        """Sağ tık işlemi"""
        self.show_context_menu(event)
    
    def prev_frame(self, event=None):
        """Önceki frame'e git"""
        if not self.frames:
            return
        
        # Mevcut frame için etiketleri kaydet
        if self.current_boxes:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
            if not save_result:
                print(f"Etiketler kaydedilemedi (önceki frame'e geçiş): {frame_path}")
            else:
                print(f"Etiketler kaydedildi (önceki frame'e geçiş): {frame_path}")
        
        # Önceki frame'e git
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            
            # Son yüklenen frame'i sıfırla
            if hasattr(self, '_last_loaded_frame'):
                self._last_loaded_frame = None
            
            # Oturum bilgilerini güncelle
            session_info = {
                "video_path": self.video_path,
                "output_dir": self.output_dir,
                "current_frame_idx": self.current_frame_idx,
                "labels": self.labels,
                "is_image_set": self.video_path is None
            }
            save_session_info(session_info, self.output_dir, self.session_file)
            
            # Yeni frame'i göster
            self.show_current_frame()
            
            # Seçili kutuları temizle
            self.selected_box_indices = []
            
            # İşlem geçmişini temizle (farklı frame'de geri alma yapılmamalı)
            self.action_history = []
    
    def next_frame(self, event=None):
        """Sonraki frame'e git"""
        if not self.frames:
            return
        
        # Mevcut frame için etiketleri kaydet
        if self.current_boxes:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
            if not save_result:
                print(f"Etiketler kaydedilemedi (sonraki frame'e geçiş): {frame_path}")
            else:
                print(f"Etiketler kaydedildi (sonraki frame'e geçiş): {frame_path}")
        
        # Sonraki frame'e git
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            
            # Son yüklenen frame'i sıfırla
            if hasattr(self, '_last_loaded_frame'):
                self._last_loaded_frame = None
            
            # Oturum bilgilerini güncelle
            session_info = {
                "video_path": self.video_path,
                "output_dir": self.output_dir,
                "current_frame_idx": self.current_frame_idx,
                "labels": self.labels,
                "is_image_set": self.video_path is None
            }
            save_session_info(session_info, self.output_dir, self.session_file)
            
            # Yeni frame'i göster
            self.show_current_frame()
            
            # Seçili kutuları temizle
            self.selected_box_indices = []
            
            # İşlem geçmişini temizle (farklı frame'de geri alma yapılmamalı)
            self.action_history = []
    
    def on_shift_mouse_down(self, event):
        """Shift tuşuna basıldığında yapılacak işlemler"""
        pass
    
    def on_shift_mouse_move(self, event):
        """Shift tuşuna basılı tutularak fare hareketi"""
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.scan_dragto(dx, dy, gain=1)
    
    def on_shift_mouse_up(self, event):
        """Shift tuşundan kalkıldığında yapılacak işlemler"""
        pass
    
    def on_mouse_wheel(self, event):
        """Fare tekerleği ile yakınlaştırma/uzaklaştırma"""
        # Windows için
        if event.num == 5 or event.delta < 0:
            self.on_zoom_out()
        elif event.num == 4 or event.delta > 0:
            self.on_zoom_in()
    
    def on_mouse_hover(self, event):
        """Fare hareketi izleme"""
        # Fare imleci bir kutunun üzerinde ise, hover indeksini güncelle
        x, y = event.x, event.y
        for idx, (x1, y1, x2, y2, _) in enumerate(self.current_boxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.hover_box_idx = idx
                break
        else:
            self.hover_box_idx = -1
    
    def update_label_select_menu(self):
        """Sağ tık menüsündeki etiket seçim alt menüsünü güncelle"""
        # Önce mevcut menüyü temizle
        self.label_select_menu.delete(0, tk.END)
        
        # Etiketleri ekle
        for label in self.labels:
            self.label_select_menu.add_command(
                label=label,
                command=lambda l=label: self.set_current_label(l)
            )
    
    def set_current_label(self, label):
        """Mevcut etiketi ayarla"""
        self.annotation_panel.current_label_var.set(label)
        self.annotation_panel.selected_label_var.set(label)
    
    def prev_page(self, event=None):
        """Önceki sayfaya git (Page Up)"""
        if not self.frames:
            return
        
        # Sayfa boyutu (ayarlanabilir)
        page_size = self.settings_panel.page_size_var.get()
        
        # Mevcut frame için etiketleri kaydet
        if self.current_boxes:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
            if not save_result:
                print(f"Etiketler kaydedilemedi (önceki sayfaya geçiş): {frame_path}")
            else:
                print(f"Etiketler kaydedildi (önceki sayfaya geçiş): {frame_path}")
        
        # Önceki sayfaya git
        new_idx = max(0, self.current_frame_idx - page_size)
        if new_idx != self.current_frame_idx:
            self.current_frame_idx = new_idx
            
            # Son yüklenen frame'i sıfırla
            if hasattr(self, '_last_loaded_frame'):
                self._last_loaded_frame = None
            
            # Oturum bilgilerini güncelle
            session_info = {
                "video_path": self.video_path,
                "output_dir": self.output_dir,
                "current_frame_idx": self.current_frame_idx,
                "labels": self.labels,
                "is_image_set": self.video_path is None
            }
            save_session_info(session_info, self.output_dir, self.session_file)
            
            # Yeni frame'i göster
            self.show_current_frame()
            
            # Seçili kutuları temizle
            self.selected_box_indices = []
            
            # İşlem geçmişini temizle (farklı frame'de geri alma yapılmamalı)
            self.action_history = []
    
    def next_page(self, event=None):
        """Sonraki sayfaya git (Page Down)"""
        if not self.frames:
            return
        
        # Sayfa boyutu (ayarlanabilir)
        page_size = self.settings_panel.page_size_var.get()
        
        # Mevcut frame için etiketleri kaydet
        if self.current_boxes:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
            if not save_result:
                print(f"Etiketler kaydedilemedi (sonraki sayfaya geçiş): {frame_path}")
            else:
                print(f"Etiketler kaydedildi (sonraki sayfaya geçiş): {frame_path}")
        
        # Sonraki sayfaya git
        new_idx = min(len(self.frames) - 1, self.current_frame_idx + page_size)
        if new_idx != self.current_frame_idx:
            self.current_frame_idx = new_idx
            
            # Son yüklenen frame'i sıfırla
            if hasattr(self, '_last_loaded_frame'):
                self._last_loaded_frame = None
            
            # Oturum bilgilerini güncelle
            session_info = {
                "video_path": self.video_path,
                "output_dir": self.output_dir,
                "current_frame_idx": self.current_frame_idx,
                "labels": self.labels,
                "is_image_set": self.video_path is None
            }
            save_session_info(session_info, self.output_dir, self.session_file)
            
            # Yeni frame'i göster
            self.show_current_frame()
            
            # Seçili kutuları temizle
            self.selected_box_indices = []
            
            # İşlem geçmişini temizle (farklı frame'de geri alma yapılmamalı)
            self.action_history = [] 

    def load_images(self):
        """Fotoğraf dosyalarını yükle"""
        image_paths = filedialog.askopenfilenames(
            title="Fotoğraf Dosyalarını Seç",
            filetypes=[("Görüntü Dosyaları", "*.jpg *.jpeg *.png *.bmp"), ("Tüm Dosyalar", "*.*")]
        )
        
        if not image_paths:
            return
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", "Fotoğraflar yüklendi. Şimdi çıktı klasörünü seçin.")
        
        # Çıktı klasörünü seç
        output_dir = filedialog.askdirectory(title="Çıktı Klasörünü Seç")
        if not output_dir:
            return
        
        # Değişkenleri ayarla
        self.video_path = None
        self.output_dir = output_dir
        
        # Çıktı klasörlerini oluştur
        if not create_output_dirs(output_dir):
            messagebox.showerror("Hata", "Çıktı klasörleri oluşturulamadı.")
            return
        
        # Frameleri temizle
        self.frames = []
        
        # Fotoğrafları yükle ve frames klasörüne kopyala
        for i, img_path in enumerate(image_paths):
            try:
                # Görüntüyü oku
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Görüntü okunamadı: {img_path}")
                    continue
                
                # RGB'ye dönüştür
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Frame dosya adını oluştur
                frame_filename = f"frame_{i:06d}.jpg"
                frame_path = os.path.join(output_dir, "frames", frame_filename)
                
                # Görüntüyü kaydet
                if not cv2.imwrite(frame_path, img):
                    print(f"Görüntü kaydedilemedi: {frame_path}")
                    continue
                
                # Frames listesine ekle
                self.frames.append((rgb_img, frame_path))
            except Exception as e:
                print(f"Hata: {e}")
        
        if not self.frames:
            messagebox.showerror("Hata", "Fotoğraflar yüklenemedi.")
            return
        
        # İlk frame'i göster
        self.current_frame_idx = 0
        
        # Son yüklenen frame'i sıfırla
        if hasattr(self, '_last_loaded_frame'):
            self._last_loaded_frame = None
        
        self.show_current_frame()
        
        # Frame bilgisini güncelle
        self.annotation_panel.update_frame_info(self.current_frame_idx, len(self.frames))
        
        # Oturum bilgilerini kaydet
        session_info = {
            "video_path": None,
            "output_dir": output_dir,
            "current_frame_idx": 0,
            "labels": self.labels,
            "is_image_set": True
        }
        save_session_info(session_info, output_dir, self.session_file)
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", f"{len(self.frames)} fotoğraf yüklendi.")
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"Fotoğraflar yüklendi: {len(self.frames)} fotoğraf")
    
    def load_video(self):
        """Video dosyasını yükle"""
        video_path = filedialog.askopenfilename(
            title="Video Dosyasını Seç",
            filetypes=[("Video Dosyaları", "*.mp4 *.avi *.mov *.mkv"), ("Tüm Dosyalar", "*.*")]
        )
        
        if not video_path:
            return
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", "Video yüklendi. Şimdi çıktı klasörünü seçin.")
        
        # Çıktı klasörünü seç
        output_dir = filedialog.askdirectory(title="Çıktı Klasörünü Seç")
        if not output_dir:
            return
        
        # Değişkenleri ayarla
        self.video_path = video_path
        self.output_dir = output_dir
        
        # Çıktı klasörlerini oluştur
        if not create_output_dirs(output_dir):
            messagebox.showerror("Hata", "Çıktı klasörleri oluşturulamadı.")
            return
        
        # Frame aralığını sor
        interval = simpledialog.askinteger("Frame Aralığı", 
                                          "Kaç frame'de bir çıkarılsın? (1-1000):", 
                                          minvalue=1, maxvalue=1000, initialvalue=30)
        if not interval:
            return
        
        # Frameleri çıkar
        self.frames = extract_frames_from_video(video_path, output_dir, interval)
        
        if not self.frames:
            messagebox.showerror("Hata", "Frameler çıkarılamadı.")
            return
        
        # İlk frame'i göster
        self.current_frame_idx = 0
        
        # Son yüklenen frame'i sıfırla
        if hasattr(self, '_last_loaded_frame'):
            self._last_loaded_frame = None
        
        self.show_current_frame()
        
        # Frame bilgisini güncelle
        self.annotation_panel.update_frame_info(self.current_frame_idx, len(self.frames))
        
        # Oturum bilgilerini kaydet
        session_info = {
            "video_path": video_path,
            "output_dir": output_dir,
            "current_frame_idx": 0,
            "labels": self.labels,
            "is_image_set": False
        }
        save_session_info(session_info, output_dir, self.session_file)
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", f"{len(self.frames)} frame çıkarıldı.")
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"Video yüklendi: {len(self.frames)} frame")
    
    def extract_frames(self):
        """Video dosyasından frameleri çıkar"""
        if not self.video_path or not self.output_dir:
            messagebox.showerror("Hata", "Önce bir video dosyası yüklemelisiniz.")
            return
        
        # Frame aralığını sor
        interval = simpledialog.askinteger("Frame Aralığı", 
                                          "Kaç frame'de bir çıkarılsın? (1-100):", 
                                          minvalue=1, maxvalue=100, initialvalue=30)
        if not interval:
            return
        
        # Frameleri çıkar
        self.frames = extract_frames_from_video(self.video_path, self.output_dir, interval)
        
        if not self.frames:
            messagebox.showerror("Hata", "Frameler çıkarılamadı.")
            return
        
        # İlk frame'i göster
        self.current_frame_idx = 0
        
        # Son yüklenen frame'i sıfırla
        if hasattr(self, '_last_loaded_frame'):
            self._last_loaded_frame = None
        
        self.show_current_frame()
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", f"{len(self.frames)} frame çıkarıldı.")
        
        # Frame bilgisini güncelle
        self.annotation_panel.update_frame_info(self.current_frame_idx, len(self.frames))
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"Frameler çıkarıldı: {len(self.frames)} frame")
    
    def resume_from_last_session(self):
        """Son oturumdan devam et"""
        # Çıktı klasörünü seç
        output_dir = filedialog.askdirectory(title="Oturum Klasörünü Seç")
        if not output_dir:
            return
        
        # Oturum bilgilerini yükle
        session_info = load_session_info(output_dir, self.session_file)
        if not session_info:
            messagebox.showerror("Hata", "Oturum bilgileri bulunamadı.")
            return
        
        # Değişkenleri ayarla
        self.video_path = session_info.get("video_path", "")
        self.output_dir = output_dir
        self.labels = session_info.get("labels", [])
        
        # Etiket listesini güncelle
        self.annotation_panel.update_label_list(self.labels)
        self.annotation_panel.update_label_menu(self.labels)
        
        # Frameleri yükle
        frames_dir = os.path.join(output_dir, "frames")
        self.frames = load_frames_from_dir(frames_dir)
        
        if not self.frames:
            messagebox.showerror("Hata", "Frameler yüklenemedi.")
            return
        
        # Son frame'e git
        self.current_frame_idx = session_info.get("current_frame_idx", 0)
        if self.current_frame_idx >= len(self.frames):
            self.current_frame_idx = 0
        
        # Son yüklenen frame'i sıfırla
        if hasattr(self, '_last_loaded_frame'):
            self._last_loaded_frame = None
        
        # Mevcut frame'i göster
        self.show_current_frame()
        
        # Frame bilgisini güncelle
        self.annotation_panel.update_frame_info(self.current_frame_idx, len(self.frames))
        
        # Kullanıcıya bilgi ver
        is_image_set = session_info.get("is_image_set", False)
        if is_image_set:
            messagebox.showinfo("Bilgi", f"Fotoğraf seti yüklendi. {len(self.frames)} fotoğraf bulundu.")
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Fotoğraf seti yüklendi: {len(self.frames)} fotoğraf")
        else:
            messagebox.showinfo("Bilgi", f"Oturum yüklendi. {len(self.frames)} frame bulundu.")
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Oturum yüklendi: {len(self.frames)} frame")
    
    def save_annotations(self, event=None, show_message=True):
        """Etiketleri kaydet"""
        if not self.frames or not self.output_dir:
            if show_message:
                messagebox.showerror("Hata", "Kaydedilecek frame veya çıktı klasörü yok.")
            return
        
        # Mevcut frame için etiketleri kaydet
        if self.current_boxes:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir, silent=True)
            if not save_result:
                if show_message:
                    messagebox.showerror("Hata", "Etiketler kaydedilemedi.")
                return
        
        # Oturum bilgilerini güncelle
        session_info = {
            "video_path": self.video_path,
            "output_dir": self.output_dir,
            "current_frame_idx": self.current_frame_idx,
            "labels": self.labels,
            "is_image_set": self.video_path is None  # Video yolu yoksa fotoğraf seti
        }
        save_session_info(session_info, self.output_dir, self.session_file)
        
        # Kullanıcıya bilgi ver
        if show_message:
            messagebox.showinfo("Bilgi", "Etiketler kaydedildi.")
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Etiketler kaydedildi: {os.path.basename(frame_path)}")
    
    def on_closing(self):
        """Uygulama kapatılırken çağrılır"""
        # Otomatik kaydetme işini iptal et
        if self.autosave_job:
            self.root.after_cancel(self.autosave_job)
            self.autosave_job = None
            
        # Eğer açık bir oturum varsa, oturum bilgilerini kaydet
        if self.frames and self.output_dir:
            # Mevcut etiketleri kaydet
            if self.current_boxes:
                frame_data, frame_path = self.frames[self.current_frame_idx]
                save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir, silent=True)
            
            # Oturum bilgilerini kaydet
            session_info = {
                "video_path": self.video_path,
                "output_dir": self.output_dir,
                "current_frame_idx": self.current_frame_idx,
                "labels": self.labels,
                "is_image_set": self.video_path is None
            }
            save_session_info(session_info, self.output_dir, self.session_file)
            
            # Klavye kısayollarını kaydet
            self.save_keyboard_shortcuts()
            
            print("Oturum bilgileri kaydedildi.")
        
        self.root.destroy()

    def goto_specific_frame_dialog(self, event=None):
        """Belirli bir frame'e gitme diyaloğu"""
        if not self.frames:
            return
        
        frame_idx = simpledialog.askinteger("Frame'e Git", 
                                           f"Frame numarası (1-{len(self.frames)}):", 
                                           minvalue=1, maxvalue=len(self.frames))
        if frame_idx:
            # Mevcut frame için etiketleri kaydet
            if self.current_boxes:
                frame_data, frame_path = self.frames[self.current_frame_idx]
                save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
                if not save_result:
                    print(f"Etiketler kaydedilemedi (belirli frame'e geçiş diyalog): {frame_path}")
                else:
                    print(f"Etiketler kaydedildi (belirli frame'e geçiş diyalog): {frame_path}")
            
            # Belirtilen frame'e git
            self.current_frame_idx = frame_idx - 1
            
            # Son yüklenen frame'i sıfırla
            if hasattr(self, '_last_loaded_frame'):
                self._last_loaded_frame = None
            
            # Oturum bilgilerini güncelle
            session_info = {
                "video_path": self.video_path,
                "output_dir": self.output_dir,
                "current_frame_idx": self.current_frame_idx,
                "labels": self.labels,
                "is_image_set": self.video_path is None
            }
            save_session_info(session_info, self.output_dir, self.session_file)
            
            # Yeni frame'i göster
            self.show_current_frame()
            
            # Seçili kutuları temizle
            self.selected_box_indices = []
            
            # İşlem geçmişini temizle (farklı frame'de geri alma yapılmamalı)
            self.action_history = [] 

    def show_current_frame(self):
        """Mevcut frame'i göster"""
        if not self.frames:
            return
        
        # Mevcut frame'i al
        frame_data, frame_path = self.frames[self.current_frame_idx]
        
        # Son yüklenen frame'i kontrol et
        if hasattr(self, '_last_loaded_frame') and self._last_loaded_frame == frame_path:
            # Aynı frame, sadece kutuları yeniden çiz
            pass
        else:
            # Yeni frame, yükle ve kutuları çiz
            self._last_loaded_frame = frame_path
            
            # Etiketleri yükle
            label_path = os.path.join(
                self.output_dir, 
                "labels", 
                os.path.splitext(os.path.basename(frame_path))[0] + ".txt"
            )
            
            if os.path.exists(label_path):
                self.current_boxes = load_annotations(frame_path, self.output_dir, self.labels)
            else:
                self.current_boxes = []
        
        # Canvas boyutlarını al
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Orijinal görüntü boyutlarını al
        img_h, img_w = frame_data.shape[:2]
        
        # Frame'i yeniden boyutlandır
        resized_frame, _ = resize_frame(frame_data, canvas_width, canvas_height, self.zoom_factor)
        
        # PhotoImage oluştur
        photo = create_photo_image(resized_frame)
        
        # Canvas'ı temizle
        self.canvas.delete("all")
        
        # Görüntüyü canvas'a yerleştir
        resized_h, resized_w = resized_frame.shape[:2]
        x_offset = (canvas_width - resized_w) // 2
        y_offset = (canvas_height - resized_h) // 2
        
        self.canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # Referansı tut
        
        # Izgara çiz
        if self.grid_enabled:
            draw_grid(self.canvas, img_w, img_h, canvas_width, canvas_height, 
                     self.grid_size, self.grid_color, self.zoom_factor)
        
        # Kutuları çiz
        if self.current_boxes:
            draw_boxes(self.canvas, self.current_boxes, img_w, img_h, canvas_width, canvas_height,
                      self.zoom_factor, self.selected_box_indices, self.label_colors, self.hover_box_idx)
        
        # Frame bilgisini güncelle
        self.annotation_panel.update_frame_info(self.current_frame_idx, len(self.frames))
    
    def add_label(self):
        """Yeni etiket ekle"""
        label = simpledialog.askstring("Etiket Ekle", "Etiket adı:")
        if label and label not in self.labels:
            self.labels.append(label)
            
            # Etiket listesini güncelle
            self.annotation_panel.update_label_list(self.labels)
            self.annotation_panel.update_label_menu(self.labels)
            
            # Etiket seçim menüsünü güncelle
            self.update_label_select_menu()
            
            # Oturum bilgilerini güncelle
            if self.output_dir:
                session_info = {
                    "video_path": self.video_path,
                    "output_dir": self.output_dir,
                    "current_frame_idx": self.current_frame_idx,
                    "labels": self.labels,
                    "is_image_set": self.video_path is None
                }
                save_session_info(session_info, self.output_dir, self.session_file)
            
            # Kullanıcıya bilgi ver
            messagebox.showinfo("Bilgi", f"Etiket eklendi: {label}") 

    def configure_label_colors(self):
        """Etiket renklerini yapılandır"""
        if not self.labels:
            messagebox.showinfo("Bilgi", "Önce etiket eklemelisiniz.")
            return
        
        # Renk seçim penceresi
        color_window = tk.Toplevel(self.root)
        color_window.title("Etiket Renklerini Ayarla")
        color_window.geometry("400x400")
        color_window.resizable(True, True)
        
        # Ana frame
        main_frame = ttk.Frame(color_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        ttk.Label(main_frame, text="Etiket Renklerini Ayarla", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Açıklama
        ttk.Label(main_frame, text="Her etiket için bir renk seçin.", 
                 wraplength=380, justify=tk.CENTER).pack(pady=5)
        
        # Etiket listesi
        label_frame = ttk.Frame(main_frame)
        label_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Renk seçim butonları
        color_buttons = {}
        
        for label in self.labels:
            frame = ttk.Frame(label_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=label, width=20).pack(side=tk.LEFT, padx=5)
            
            # Mevcut renk
            current_color = self.label_colors.get(label, "#FF0000")  # Varsayılan kırmızı
            
            # Renk butonu
            color_var = tk.StringVar(value=current_color)
            color_button = ttk.Button(frame, text="Renk Seç", 
                                     command=lambda l=label, v=color_var: self.choose_color(l, v))
            color_button.pack(side=tk.LEFT, padx=5)
            
            # Renk örneği
            color_sample = tk.Canvas(frame, width=30, height=20, bg=current_color)
            color_sample.pack(side=tk.LEFT, padx=5)
            
            color_buttons[label] = (color_var, color_sample)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", 
                  command=lambda: self.save_label_colors(color_buttons, color_window)).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="İptal", 
                  command=color_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def choose_color(self, label, color_var):
        """Renk seçim diyaloğu"""
        from tkinter import colorchooser
        
        # Mevcut renk
        current_color = color_var.get()
        
        # Renk seçim diyaloğu
        color = colorchooser.askcolor(initialcolor=current_color, title=f"{label} için renk seç")
        
        if color[1]:  # Renk seçildiyse
            color_var.set(color[1])
            
            # Renk örneğini güncelle
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Canvas) and widget.winfo_width() == 30 and widget.winfo_height() == 20:
                    widget.config(bg=color[1])
    
    def save_label_colors(self, color_buttons, window):
        """Etiket renklerini kaydet"""
        # Renkleri güncelle
        for label, (color_var, _) in color_buttons.items():
            self.label_colors[label] = color_var.get()
        
        # Kutuları yeniden çiz
        self.show_current_frame()
        
        # Kullanıcıya bilgi ver
        messagebox.showinfo("Bilgi", "Etiket renkleri kaydedildi.")
        
        # Pencereyi kapat
        window.destroy()
    
    def select_all_boxes(self):
        """Tüm kutuları seç"""
        if not self.current_boxes:
            return
        
        # Tüm kutuların indekslerini seç
        self.selected_box_indices = list(range(len(self.current_boxes)))
        
        # Kutuları yeniden çiz
        self.show_current_frame()
    
    def deselect_all(self):
        """Tüm seçimleri kaldır"""
        if not self.selected_box_indices:
            return
        
        # Seçimleri temizle
        self.selected_box_indices = []
        
        # Kutuları yeniden çiz
        self.show_current_frame()
    
    def delete_selected_box(self):
        """Seçili kutuları sil"""
        if not self.selected_box_indices:
            return
        
        # İşlem geçmişine ekle
        self.action_history.append(("delete", self.current_boxes.copy(), self.selected_box_indices.copy()))
        
        # Seçili kutuları sil (büyükten küçüğe doğru sıralayarak)
        for idx in sorted(self.selected_box_indices, reverse=True):
            if 0 <= idx < len(self.current_boxes):
                self.current_boxes.pop(idx)
        
        # Seçimleri temizle
        self.selected_box_indices = []
        
        # Kutuları yeniden çiz
        self.show_current_frame()
        
        # Etiketleri hemen kaydet
        if self.frames:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
            if not save_result:
                print(f"Etiketler kaydedilemedi (kutu silme sonrası): {frame_path}")
            else:
                print(f"Etiketler kaydedildi (kutu silme sonrası): {frame_path}")
    
    def delete_box_or_selected(self):
        """Seçili kutuları veya son kutuyu sil"""
        if self.selected_box_indices:
            self.delete_selected_box()
        elif self.current_boxes:
            # Son kutuyu sil
            self.action_history.append(("delete", self.current_boxes.copy(), [len(self.current_boxes) - 1]))
            self.current_boxes.pop()
            
            # Kutuları yeniden çiz
            self.show_current_frame()
            
            # Etiketleri hemen kaydet
            if self.frames:
                frame_data, frame_path = self.frames[self.current_frame_idx]
                save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir)
                if not save_result:
                    print(f"Etiketler kaydedilemedi (son kutu silme sonrası): {frame_path}")
                else:
                    print(f"Etiketler kaydedildi (son kutu silme sonrası): {frame_path}") 

    def configure_autosave(self):
        """Otomatik kaydetme ayarlarını yapılandır"""
        # Otomatik kaydetme penceresi
        autosave_window = tk.Toplevel(self.root)
        autosave_window.title("Otomatik Kaydetme Ayarları")
        autosave_window.geometry("400x200")
        autosave_window.resizable(False, False)
        
        # Ana frame
        main_frame = ttk.Frame(autosave_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        ttk.Label(main_frame, text="Otomatik Kaydetme Ayarları", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        # Otomatik kaydetme seçeneği
        autosave_var = tk.BooleanVar(value=self.autosave_enabled)
        ttk.Checkbutton(main_frame, text="Otomatik kaydetmeyi etkinleştir", 
                       variable=autosave_var).pack(anchor=tk.W, pady=5)
        
        # Aralık seçimi
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(interval_frame, text="Kaydetme aralığı (saniye):").pack(side=tk.LEFT, padx=5)
        
        interval_var = tk.IntVar(value=self.autosave_interval // 1000)
        interval_spinbox = ttk.Spinbox(interval_frame, from_=10, to=600, increment=10, 
                                      textvariable=interval_var, width=5)
        interval_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", 
                  command=lambda: self.save_autosave_settings(autosave_var.get(), interval_var.get(), autosave_window)).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="İptal", 
                  command=autosave_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def save_autosave_settings(self, enabled, interval, window):
        """Otomatik kaydetme ayarlarını kaydet"""
        # Ayarları güncelle
        self.autosave_enabled = enabled
        self.autosave_interval = interval * 1000  # Saniyeden milisaniyeye çevir
        
        # Mevcut otomatik kaydetme işini iptal et
        if self.autosave_job:
            self.root.after_cancel(self.autosave_job)
            self.autosave_job = None
        
        # Otomatik kaydetme etkinse, yeni iş planla
        if self.autosave_enabled:
            self.autosave_job = self.root.after(self.autosave_interval, self.autosave)
        
        # Kullanıcıya bilgi ver
        if enabled:
            messagebox.showinfo("Bilgi", f"Otomatik kaydetme etkinleştirildi. Aralık: {interval} saniye.")
        else:
            messagebox.showinfo("Bilgi", "Otomatik kaydetme devre dışı bırakıldı.")
        
        # Pencereyi kapat
        window.destroy()
    
    def autosave(self):
        """Otomatik kaydetme işlemi"""
        if self.frames and self.output_dir and self.current_boxes:
            frame_data, frame_path = self.frames[self.current_frame_idx]
            save_result = save_annotations(self.current_boxes, self.labels, frame_path, self.output_dir, silent=True)
            if save_result:
                # Oturum bilgilerini güncelle
                session_info = {
                    "video_path": self.video_path,
                    "output_dir": self.output_dir,
                    "current_frame_idx": self.current_frame_idx,
                    "labels": self.labels,
                    "is_image_set": self.video_path is None
                }
                save_session_info(session_info, self.output_dir, self.session_file)
                
                # Durum çubuğunu güncelle
                self.status_bar.config(text=f"Otomatik kaydedildi: {os.path.basename(frame_path)}")
            else:
                print(f"Otomatik kaydetme başarısız: {frame_path}")
        
        # Bir sonraki otomatik kaydetme işini planla
        if self.autosave_enabled:
            self.autosave_job = self.root.after(self.autosave_interval, self.autosave)
    
    def toggle_autosave(self):
        """Otomatik kaydetmeyi aç/kapat"""
        self.autosave_enabled = not self.autosave_enabled
        
        # Mevcut otomatik kaydetme işini iptal et
        if self.autosave_job:
            self.root.after_cancel(self.autosave_job)
            self.autosave_job = None
        
        # Otomatik kaydetme etkinse, yeni iş planla
        if self.autosave_enabled:
            self.autosave_job = self.root.after(self.autosave_interval, self.autosave)
            self.status_bar.config(text=f"Otomatik kaydetme etkinleştirildi. Aralık: {self.autosave_interval // 1000} saniye.")
        else:
            self.status_bar.config(text="Otomatik kaydetme devre dışı bırakıldı.")
    
    def update_autosave_interval(self, event=None):
        """Otomatik kaydetme aralığını güncelle"""
        try:
            # Ayarlar panelinden değeri al
            interval_str = self.settings_panel.autosave_interval_var.get()
            interval = int(interval_str)
            
            # Geçerli bir aralık olduğundan emin ol (en az 10 saniye)
            if interval < 10:
                interval = 10
                self.settings_panel.autosave_interval_var.set(str(interval))
            
            # Aralığı güncelle
            self.autosave_interval = interval * 1000  # Saniyeden milisaniyeye çevir
            
            # Mevcut otomatik kaydetme işini iptal et
            if self.autosave_job:
                self.root.after_cancel(self.autosave_job)
                self.autosave_job = None
            
            # Otomatik kaydetme etkinse, yeni iş planla
            if self.autosave_enabled:
                self.autosave_job = self.root.after(self.autosave_interval, self.autosave)
            
            self.status_bar.config(text=f"Otomatik kaydetme aralığı güncellendi: {interval} saniye.")
        except ValueError:
            # Geçersiz değer girilirse, eski değeri geri yükle
            self.settings_panel.autosave_interval_var.set(str(self.autosave_interval // 1000))
            self.status_bar.config(text="Geçersiz aralık değeri. Lütfen bir sayı girin.")
    
    def update_grid_size(self, event=None):
        """Izgara boyutunu güncelle"""
        try:
            new_size = int(self.settings_panel.grid_size_var.get())
            if new_size > 0:
                self.grid_size = new_size
                self.show_current_frame()
                self.status_bar.config(text=f"Izgara boyutu {new_size} olarak güncellendi")
        except ValueError:
            # Geçersiz değer girilirse eski değeri geri yükle
            self.settings_panel.grid_size_var.set(str(self.grid_size))
            self.status_bar.config(text="Geçersiz ızgara boyutu. Lütfen bir sayı girin.")
        return "break"  # Prevent default behavior for Return key

    def create_context_menu(self):
        """Sağ tık menüsünü oluştur"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        
        # Etiket seçim alt menüsü
        self.label_select_menu = tk.Menu(self.context_menu, tearoff=0)
        self.context_menu.add_cascade(label="Etiket Seç", menu=self.label_select_menu)
        
        # Etiketleri ekle
        for label in self.labels:
            self.label_select_menu.add_command(
                label=label,
                command=lambda l=label: self.set_current_label(l)
            )
        
        # Diğer menü öğeleri
        self.context_menu.add_command(label="Kutuyu Sil", command=self.delete_selected_box)
        self.context_menu.add_command(label="Tümünü Seç", command=self.select_all_boxes)
        self.context_menu.add_command(label="Seçimi Kaldır", command=self.deselect_all)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Izgara Aç/Kapat", command=self.on_toggle_grid)
        
        # Canvas'a sağ tık olayını bağla
        self.canvas.bind("<ButtonPress-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Sağ tık menüsünü göster"""
        # Etiket seçim menüsünü güncelle
        self.update_label_select_menu()
        
        # Menüyü göster
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()