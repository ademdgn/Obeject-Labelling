import os
import json
import cv2
import numpy as np

def create_output_dirs(output_dir):
    """Çıktı klasörlerini oluştur"""
    try:
        os.makedirs(os.path.join(output_dir, "frames"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "labels"), exist_ok=True)
        return True
    except Exception as e:
        print(f"Çıktı klasörleri oluşturulamadı: {e}")
        return False

def save_session_info(session_info, output_dir, session_file="session_info.json"):
    """Oturum bilgilerini JSON dosyasına kaydet"""
    if not output_dir:
        return False
    
    session_file_path = os.path.join(output_dir, session_file)
    
    try:
        with open(session_file_path, 'w') as f:
            json.dump(session_info, f)
        return True
    except Exception as e:
        print(f"Oturum bilgileri kaydedilemedi: {e}")
        return False

def load_session_info(output_dir, session_file="session_info.json"):
    """Oturum bilgilerini JSON dosyasından yükle"""
    if not output_dir:
        return None
    
    session_file_path = os.path.join(output_dir, session_file)
    
    if not os.path.exists(session_file_path):
        return None
    
    try:
        with open(session_file_path, 'r') as f:
            session_info = json.load(f)
        return session_info
    except Exception as e:
        print(f"Oturum bilgileri yüklenemedi: {e}")
        return None

def extract_frames_from_video(video_path, output_dir, interval=30):
    """Video dosyasından frameleri çıkar ve kaydet"""
    if not video_path or not output_dir:
        print("Video yolu veya çıktı klasörü belirtilmemiş.")
        return []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Video açılamadı: {video_path}")
            return []
        
        # Frames klasörünün var olduğundan emin ol
        frames_dir = os.path.join(output_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        frames = []
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % interval == 0:
                # Frame'i kaydet
                frame_path = os.path.join(frames_dir, f"frame_{saved_count:06d}.jpg")
                if not cv2.imwrite(frame_path, frame):
                    print(f"Frame kaydedilemedi: {frame_path}")
                    frame_count += 1
                    continue
                
                # RGB'ye dönüştür ve listeye ekle
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append((rgb_frame, frame_path))
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        
        if not frames:
            print("Hiç frame çıkarılamadı.")
        else:
            print(f"{saved_count} frame çıkarıldı.")
        
        return frames
    except Exception as e:
        print(f"Frame çıkarma işlemi sırasında hata oluştu: {e}")
        return []

def load_frames_from_dir(frames_dir):
    """Klasörden frameleri yükle"""
    frames = []
    
    if not frames_dir or not os.path.exists(frames_dir):
        print(f"Frames klasörü bulunamadı: {frames_dir}")
        return frames
    
    try:
        # Frame dosyalarını bul ve sırala
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".jpg")])
        
        if not frame_files:
            print(f"Frames klasöründe frame bulunamadı: {frames_dir}")
            return frames
        
        for frame_file in frame_files:
            try:
                frame_path = os.path.join(frames_dir, frame_file)
                frame = cv2.imread(frame_path)
                
                if frame is None:
                    print(f"Frame okunamadı: {frame_path}")
                    continue
                
                # BGR'den RGB'ye dönüştür
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append((rgb_frame, frame_path))
            except Exception as e:
                print(f"Frame yüklenirken hata oluştu: {frame_file} - {e}")
        
        print(f"{len(frames)} frame yüklendi.")
        return frames
    except Exception as e:
        print(f"Frameler yüklenirken hata oluştu: {e}")
        return frames

def get_label_path(frame_path, output_dir):
    """Frame yolundan etiket dosyası yolunu oluştur"""
    frame_name = os.path.basename(frame_path)
    frame_name_without_ext = os.path.splitext(frame_name)[0]
    return os.path.join(output_dir, "labels", f"{frame_name_without_ext}.txt")

def save_annotations(boxes, labels, frame_path, output_dir, silent=True):
    """Etiketleri YOLO formatında kaydet"""
    if not frame_path or not output_dir:
        if not silent:
            print("Kaydetmek için gerekli bilgiler eksik: frame_path veya output_dir yok.")
        return False
    
    if not labels:
        if not silent:
            print("Etiket listesi boş. Önce etiket eklemelisiniz.")
        return False
    
    if not boxes:
        # Boş kutu listesi geçerli bir durum, boş bir dosya oluştur
        label_path = get_label_path(frame_path, output_dir)
        try:
            # Etiket klasörünün var olduğundan emin ol
            os.makedirs(os.path.dirname(label_path), exist_ok=True)
            
            # Boş dosya oluştur
            with open(label_path, 'w') as f:
                pass
            
            if not silent:
                print(f"Boş etiket dosyası oluşturuldu: {label_path}")
            return True
        except Exception as e:
            if not silent:
                print(f"Boş etiket dosyası oluşturulamadı: {e}")
            return False
    
    # Frame boyutlarını al
    frame = cv2.imread(frame_path)
    if frame is None:
        if not silent:
            print(f"Frame okunamadı: {frame_path}")
        return False
    
    img_h, img_w = frame.shape[:2]
    
    # YOLO formatında etiket dosyası oluştur
    label_path = get_label_path(frame_path, output_dir)
    
    try:
        # Etiket klasörünün var olduğundan emin ol
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        
        with open(label_path, 'w') as f:
            for box in boxes:
                x1, y1, x2, y2, label = box
                
                # Sınıf ID'sini bul
                try:
                    class_id = labels.index(label)
                except ValueError:
                    if not silent:
                        print(f"Etiket listede bulunamadı: {label}, mevcut etiketler: {labels}")
                    continue
                
                # YOLO formatına dönüştür (x_center, y_center, width, height)
                x_center = (x1 + x2) / (2 * img_w)
                y_center = (y1 + y2) / (2 * img_h)
                width = (x2 - x1) / img_w
                height = (y2 - y1) / img_h
                
                # Değerlerin 0-1 aralığında olduğundan emin ol
                x_center = max(0, min(x_center, 1))
                y_center = max(0, min(y_center, 1))
                width = max(0, min(width, 1))
                height = max(0, min(height, 1))
                
                f.write(f"{class_id} {x_center} {y_center} {width} {height}\n")
        
        if not silent:
            print(f"Etiketler başarıyla kaydedildi: {label_path}")
        return True
    except Exception as e:
        if not silent:
            print(f"Etiketler kaydedilemedi: {e}")
        return False

def load_annotations(frame_path, output_dir, labels):
    """YOLO formatındaki etiketleri yükle"""
    boxes = []
    
    if not frame_path or not output_dir:
        print("Yüklemek için gerekli bilgiler eksik.")
        return boxes
    
    label_path = get_label_path(frame_path, output_dir)
    if not os.path.exists(label_path):
        print(f"Etiket dosyası bulunamadı: {label_path}")
        return boxes
    
    # Frame boyutlarını al
    frame = cv2.imread(frame_path)
    if frame is None:
        print(f"Frame okunamadı: {frame_path}")
        return boxes
    
    img_h, img_w = frame.shape[:2]
    
    try:
        with open(label_path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 5:
                try:
                    class_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                    
                    # YOLO formatından piksel koordinatlarına dönüştür
                    x1 = int((x_center - width/2) * img_w)
                    y1 = int((y_center - height/2) * img_h)
                    x2 = int((x_center + width/2) * img_w)
                    y2 = int((y_center + height/2) * img_h)
                    
                    # Koordinatları sınırlar içinde tut
                    x1 = max(0, min(x1, img_w - 1))
                    y1 = max(0, min(y1, img_h - 1))
                    x2 = max(0, min(x2, img_w - 1))
                    y2 = max(0, min(y2, img_h - 1))
                    
                    # Eğer sınıf ID'si etiket listesinde yoksa, atla
                    if 0 <= class_id < len(labels):
                        label = labels[class_id]
                        boxes.append((x1, y1, x2, y2, label))
                    else:
                        print(f"Geçersiz sınıf ID'si: {class_id}, etiket sayısı: {len(labels)}")
                except (ValueError, IndexError) as e:
                    print(f"Etiket satırı ayrıştırılamadı: {line.strip()} - {e}")
    except Exception as e:
        print(f"Etiketler yüklenemedi: {e}")
    
    return boxes 