import cv2
import numpy as np
from PIL import Image, ImageTk

def resize_frame(frame, width, height, zoom_factor=1.0):
    """Frame'i belirtilen boyuta yeniden boyutlandır"""
    h, w = frame.shape[:2]
    
    # Temel ölçeklendirme faktörünü hesapla (görüntüyü pencereye sığdırmak için)
    base_scale = min(width / w, height / h)
    
    # Zoom faktörünü uygula
    final_scale = base_scale * zoom_factor
    
    # Yeni boyutları hesapla
    new_w = int(w * final_scale)
    new_h = int(h * final_scale)
    
    # Frame'i yeniden boyutlandır
    resized_frame = cv2.resize(frame, (new_w, new_h))
    
    # Tutarlılık için zoom_factor'ü döndür
    return resized_frame, zoom_factor

def create_photo_image(frame):
    """OpenCV frame'inden Tkinter PhotoImage oluştur"""
    return ImageTk.PhotoImage(image=Image.fromarray(frame))

def draw_grid(canvas, img_width, img_height, canvas_width, canvas_height, 
              grid_size, grid_color, zoom_factor=1.0):
    """Canvas üzerine ızgara çiz"""
    # Görüntü boyutlarını hesapla
    scaled_w = int(img_width * zoom_factor)
    scaled_h = int(img_height * zoom_factor)
    
    # Görüntünün canvas üzerindeki konumu
    offset_x = (canvas_width - scaled_w) // 2
    offset_y = (canvas_height - scaled_h) // 2
    
    # Yatay çizgiler
    for y in range(0, scaled_h, int(grid_size * zoom_factor)):
        canvas.create_line(
            offset_x, offset_y + y, 
            offset_x + scaled_w, offset_y + y,
            fill=grid_color, tags="grid"
        )
    
    # Dikey çizgiler
    for x in range(0, scaled_w, int(grid_size * zoom_factor)):
        canvas.create_line(
            offset_x + x, offset_y,
            offset_x + x, offset_y + scaled_h,
            fill=grid_color, tags="grid"
        )

def canvas_to_image_coords(canvas_x, canvas_y, img_width, img_height, 
                          canvas_width, canvas_height, zoom_factor):
    """Canvas koordinatlarını görüntü koordinatlarına dönüştür"""
    # Canvas merkezleme ofsetini hesapla
    offset_x = (canvas_width - img_width * zoom_factor) // 2
    offset_y = (canvas_height - img_height * zoom_factor) // 2
    
    # Canvas koordinatlarından görüntü koordinatlarına dönüştür
    img_x = int((canvas_x - offset_x) / zoom_factor)
    img_y = int((canvas_y - offset_y) / zoom_factor)
    
    return img_x, img_y

def image_to_canvas_coords(img_x, img_y, img_width, img_height, 
                          canvas_width, canvas_height, zoom_factor):
    """Görüntü koordinatlarını canvas koordinatlarına dönüştür"""
    # Canvas merkezleme ofsetini hesapla
    offset_x = (canvas_width - img_width * zoom_factor) // 2
    offset_y = (canvas_height - img_height * zoom_factor) // 2
    
    # Görüntü koordinatlarından canvas koordinatlarına dönüştür
    canvas_x = int(img_x * zoom_factor) + offset_x
    canvas_y = int(img_y * zoom_factor) + offset_y
    
    return canvas_x, canvas_y 