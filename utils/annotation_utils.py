import cv2
import numpy as np

def find_box_at_position(img_x, img_y, boxes):
    """Belirtilen konumda bir kutu var mı kontrol et"""
    # Önce kutunun içinde mi kontrol et
    for i, box in enumerate(boxes):
        x1, y1, x2, y2, _ = box
        # Kutunun içinde mi kontrol et (kenarlar dahil)
        if x1 <= img_x <= x2 and y1 <= img_y <= y2:
            return i
    return -1

def draw_boxes(canvas, boxes, img_width, img_height, canvas_width, canvas_height, 
              zoom_factor, selected_indices, label_colors=None, hover_index=-1):
    """Canvas üzerine kutuları çiz"""
    if not boxes:
        return
    
    # Önce tüm kutu ve etiketleri temizle
    canvas.delete("box")
    canvas.delete("label")
    canvas.delete("overlay")
    
    # Etiket renkleri yoksa varsayılan olarak kırmızı kullan
    if label_colors is None:
        label_colors = {}
    
    # Canvas merkezleme ofsetini hesapla
    offset_x = (canvas_width - img_width * zoom_factor) // 2
    offset_y = (canvas_height - img_height * zoom_factor) // 2
    
    # Eğer fare bir kutunun üzerindeyse, tüm ekranı karartacak bir overlay oluştur
    if hover_index >= 0:
        # Tüm ekranı kaplayan karartma katmanı
        canvas.create_rectangle(
            0, 0, canvas_width, canvas_height,
            fill="black", stipple="gray50", tags="overlay"
        )
    
    # Tüm kutuları çiz
    for i, box in enumerate(boxes):
        x1, y1, x2, y2, label = box
        
        # Koordinatları ölçeklendir
        x1_scaled = int(x1 * zoom_factor)
        y1_scaled = int(y1 * zoom_factor)
        x2_scaled = int(x2 * zoom_factor)
        y2_scaled = int(y2 * zoom_factor)
        
        # Kutuyu çiz - seçili kutu farklı renkte
        # Etiket için özel renk varsa kullan, yoksa varsayılan renkleri kullan
        outline_color = label_colors.get(label, "red")
        
        # Seçili kutular için farklı renk ve kalınlık
        if i in selected_indices:
            outline_color = "yellow"  # Seçili kutu her zaman sarı
            width = 3
        elif i == hover_index:
            outline_color = "cyan"  # Fare üzerindeyken turkuaz
            width = 3
            
            # Hover durumunda, kutunun içini yarı saydam göster (overlay üzerine)
            canvas.create_rectangle(
                x1_scaled + offset_x,
                y1_scaled + offset_y,
                x2_scaled + offset_x,
                y2_scaled + offset_y,
                fill="cyan", stipple="gray25", outline="", tags="overlay"
            )
        else:
            width = 2
        
        # Kenarlık çiz
        canvas.create_rectangle(
            x1_scaled + offset_x,
            y1_scaled + offset_y,
            x2_scaled + offset_x,
            y2_scaled + offset_y,
            outline=outline_color, width=width, fill="", tags=("box", f"box_outline_{i}")
        )
        
        # Etiketi çiz
        canvas.create_text(
            x1_scaled + offset_x,
            y1_scaled + offset_y - 10,
            text=label, fill=outline_color, anchor="sw", tags=("label", f"label_{i}")
        )

def move_box(box, dx, dy, img_width, img_height):
    """Kutuyu belirtilen miktarda taşı"""
    x1, y1, x2, y2, label = box
    
    # Yeni koordinatlar
    new_x1 = x1 + dx
    new_y1 = y1 + dy
    new_x2 = x2 + dx
    new_y2 = y2 + dy
    
    # Sınırları kontrol et
    if new_x1 >= 0 and new_x2 < img_width and new_y1 >= 0 and new_y2 < img_height:
        return (new_x1, new_y1, new_x2, new_y2, label)
    
    return box

def resize_box(box, x1_delta, y1_delta, x2_delta, y2_delta, img_width, img_height):
    """Kutuyu yeniden boyutlandır"""
    x1, y1, x2, y2, label = box
    
    # Yeni koordinatlar
    new_x1 = x1 + x1_delta
    new_y1 = y1 + y1_delta
    new_x2 = x2 + x2_delta
    new_y2 = y2 + y2_delta
    
    # Sınırları kontrol et
    new_x1 = max(0, min(new_x1, img_width - 1))
    new_y1 = max(0, min(new_y1, img_height - 1))
    new_x2 = max(0, min(new_x2, img_width - 1))
    new_y2 = max(0, min(new_y2, img_height - 1))
    
    # Kutunun geçerli olduğundan emin ol (x2 > x1 ve y2 > y1)
    if new_x2 > new_x1 and new_y2 > new_y1:
        return (new_x1, new_y1, new_x2, new_y2, label)
    
    return box 