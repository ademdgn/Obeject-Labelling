import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class AnnotationPanel:
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        
        # Ana frame
        self.frame = ttk.LabelFrame(parent, text="Etiketleme Araçları")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame bilgisi
        self.frame_info_frame = ttk.Frame(self.frame)
        self.frame_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.frame_info_frame, text="Frame:").pack(side=tk.LEFT)
        self.frame_info_label = ttk.Label(self.frame_info_frame, text="0/0")
        self.frame_info_label.pack(side=tk.LEFT, padx=5)
        
        # Frame'e gitme
        self.goto_frame = ttk.Frame(self.frame)
        self.goto_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.goto_frame, text="Frame No:").pack(side=tk.LEFT)
        self.goto_entry = ttk.Entry(self.goto_frame, width=8)
        self.goto_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.goto_frame, text="Git", command=self.main_window.goto_specific_frame_dialog).pack(side=tk.LEFT)
        
        # Etiket ekleme
        self.label_frame = ttk.Frame(self.frame)
        self.label_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.label_frame, text="Etiket Ekle", command=self.main_window.add_label).pack(side=tk.LEFT)
        
        # Mevcut etiket seçimi
        self.current_label_frame = ttk.Frame(self.frame)
        self.current_label_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.current_label_frame, text="Mevcut Etiket:").pack(side=tk.LEFT)
        
        self.current_label_var = tk.StringVar(value="Etiket seçin")
        self.current_label_menu = ttk.Combobox(self.current_label_frame, 
                                              textvariable=self.current_label_var,
                                              state="readonly")
        self.current_label_menu.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Etiket listesi
        self.label_list_frame = ttk.LabelFrame(self.frame, text="Etiketler")
        self.label_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Radio button için değişken
        self.selected_label_var = tk.StringVar()
        
        # Etiket listesi için scrollbar
        self.label_scrollbar = ttk.Scrollbar(self.label_list_frame)
        self.label_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Etiket listesi için canvas ve iç frame (scrollable içerik için)
        self.label_canvas = tk.Canvas(self.label_list_frame, yscrollcommand=self.label_scrollbar.set)
        self.label_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.label_scrollbar.config(command=self.label_canvas.yview)
        
        self.label_inner_frame = ttk.Frame(self.label_canvas)
        self.label_canvas_window = self.label_canvas.create_window((0, 0), window=self.label_inner_frame, anchor=tk.NW)
        
        # Canvas boyutlandırma olayları
        self.label_inner_frame.bind("<Configure>", self._on_frame_configure)
        self.label_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Navigasyon butonları
        self.nav_frame = ttk.Frame(self.frame)
        self.nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.nav_frame, text="◀ Önceki", command=self.main_window.prev_frame).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.nav_frame, text="Sonraki ▶", command=self.main_window.next_frame).pack(side=tk.RIGHT, padx=5)
    
    def update_frame_info(self, current_idx, total_frames):
        """Frame bilgisini güncelle"""
        self.frame_info_label.config(text=f"{current_idx + 1}/{total_frames}")
    
    def update_label_list(self, labels):
        """Etiket listesini güncelle"""
        # Önce mevcut etiketleri temizle
        for widget in self.label_inner_frame.winfo_children():
            widget.destroy()
        
        # Etiketleri ekle
        for i, label in enumerate(labels):
            frame = ttk.Frame(self.label_inner_frame)
            frame.pack(fill=tk.X, padx=2, pady=2)
            
            # Radio button ekle
            radio = ttk.Radiobutton(frame, variable=self.selected_label_var, value=label,
                                   command=lambda l=label: self.on_label_selected(l))
            radio.pack(side=tk.LEFT)
            
            # Etiket adı
            ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=5)
            
            # Etiket silme butonu
            ttk.Button(frame, text="Sil", width=5,
                      command=lambda l=label: self.delete_label(l)).pack(side=tk.RIGHT)
        
        # İlk etiketi seç (eğer varsa)
        if labels:
            self.selected_label_var.set(labels[0])
            self.current_label_var.set(labels[0])
        
        # Canvas'ı güncelle
        self.label_inner_frame.update_idletasks()
        self.label_canvas.config(scrollregion=self.label_canvas.bbox("all"))
    
    def update_label_menu(self, labels):
        """Etiket açılır menüsünü güncelle"""
        self.current_label_menu['values'] = labels
        
        # Eğer mevcut seçili etiket listede yoksa, ilk etiketi seç
        current_label = self.current_label_var.get()
        if current_label not in labels and labels:
            self.current_label_var.set(labels[0])
    
    def on_label_selected(self, label):
        """Radio button ile etiket seçildiğinde"""
        self.current_label_var.set(label)
    
    def delete_label(self, label):
        """Etiketi sil"""
        if messagebox.askyesno("Etiket Sil", f"'{label}' etiketini silmek istediğinize emin misiniz?"):
            # Etiket listesinden kaldır
            if label in self.main_window.labels:
                self.main_window.labels.remove(label)
                
                # Etiket listesini güncelle
                self.update_label_list(self.main_window.labels)
                self.update_label_menu(self.main_window.labels)
                
                # Eğer silinen etiket mevcut seçili etiketse, başka bir etiket seç
                if self.current_label_var.get() == label:
                    if self.main_window.labels:
                        self.current_label_var.set(self.main_window.labels[0])
                    else:
                        self.current_label_var.set("Etiket seçin")
                
                # Oturum bilgilerini güncelle
                if self.main_window.output_dir:
                    session_info = {
                        "video_path": self.main_window.video_path,
                        "output_dir": self.main_window.output_dir,
                        "current_frame_idx": self.main_window.current_frame_idx,
                        "labels": self.main_window.labels,
                        "is_image_set": self.main_window.video_path is None
                    }
                    from utils.file_utils import save_session_info
                    save_session_info(session_info, self.main_window.output_dir, self.main_window.session_file)
    
    def _on_frame_configure(self, event):
        """İç frame boyutu değiştiğinde scrollbar'ı güncelle"""
        self.label_canvas.configure(scrollregion=self.label_canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Canvas boyutu değiştiğinde iç frame genişliğini güncelle"""
        self.label_canvas.itemconfig(self.label_canvas_window, width=event.width) 