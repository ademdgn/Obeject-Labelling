# YOLOv11 Veri Seti Hazırlama Aracı

Bu uygulama, YOLO (You Only Look Once) nesne algılama modelleri için eğitim veri seti hazırlamayı kolaylaştıran bir görsel etiketleme aracıdır.

## Özellikler

- Video dosyalarından frame çıkarma
- Fotoğraf setlerini yükleme ve düzenleme
- Etiket oluşturma ve düzenleme
- YOLO formatında etiket kaydetme
- Otomatik kaydetme
- Izgara modu ile hassas etiketleme
- Yakınlaştırma/uzaklaştırma
- Özelleştirilebilir klavye kısayolları
- İleri/geri alma işlemleri (Undo/Redo)
- Oturum kaydetme ve devam etme
- Çoklu kutu seçimi ve toplu düzenleme
- Etiket renklerini özelleştirme
- Büyük görüntüleri rahatlıkla etiketleme

## Kurulum

1. Gerekli kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
```

2. Uygulamayı çalıştırın:

```bash
python main.py
```

## Kullanım

1. **Video Yükleme**: "Dosya > Video Yükle" menüsünden bir video dosyası seçin.
2. **Fotoğraf Yükleme**: "Dosya > Fotoğraf Yükle" menüsünden bir fotoğraf seti seçin.
3. **Son Oturumdan Devam**: "Dosya > Son Oturumdan Devam Et" menüsünden önceki çalışmaya devam edin.
4. **Etiket Ekleme**: "Etiket Ekle" butonuna tıklayarak yeni etiketler ekleyin.
5. **Etiketleme**: Bir etiket seçin ve canvas üzerinde kutu çizerek nesneleri etiketleyin.
6. **Kaydetme**: "Etiketleri Kaydet" butonuna tıklayarak veya Ctrl+S kısayolunu kullanarak etiketleri kaydedin.
7. **Geri Alma**: Ctrl+Z kısayolu ile son işlemi geri alın.
8. **Yeniden Yapma**: Ctrl+Y kısayolu ile geri alınan işlemi yeniden yapın.
9. **Klavye Kısayolları**: "Ayarlar > Klavye Kısayolları" menüsünden kısayolları özelleştirin.

## Kısayollar

- **Sağ/Sol Ok**: Sonraki/önceki frame
- **Page Up/Page Down**: Sayfa sayfa ileri/geri gitme
- **Ctrl+S**: Etiketleri kaydet
- **Ctrl+Z**: Son işlemi geri al
- **Ctrl+Y**: Son geri alınan işlemi yeniden yap
- **Ctrl+G**: Izgara modunu aç/kapat
- **Ctrl+F**: Belirli bir frame'e git
- **Ctrl+A**: Tüm kutuları seç
- **ESC**: Seçimi kaldır
- **Delete**: Seçili kutuları sil
- **Ctrl+Plus/Minus**: Yakınlaştır/Uzaklaştır
- **Ctrl+0**: Yakınlaştırmayı sıfırla
- **Shift+Tıklama**: Kutuları taşı
- **Ctrl+Tıklama**: Çoklu seçim

## Geliştirme

### Proje Yapısı

- `main.py`: Ana uygulama başlangıç noktası
- `gui/`: Kullanıcı arayüzü bileşenleri
  - `main_window.py`: Ana pencere ve uygulama mantığı
  - `annotation_panel.py`: Etiketleme paneli
  - `settings_panel.py`: Ayarlar paneli
  - `menu_bar.py`: Menü çubuğu
- `utils/`: Yardımcı fonksiyonlar
  - `annotation_utils.py`: Etiketleme işlemleri
  - `file_utils.py`: Dosya işlemleri
  - `image_utils.py`: Görüntü işleme

### Yeni Özellikler (v1.1)

- **İleri/geri alma (Undo/Redo)**: Artık etiketleme işlemlerinde yapılan değişiklikler geri alınabilir ve yeniden yapılabilir.
- **Gelişmiş koordinat dönüşümü**: Büyük boyutlu görüntülerde daha doğru etiketleme için koordinat dönüşüm sistemi iyileştirildi.
- **Hover efekti**: Fare imleci bir kutu üzerine geldiğinde görsel geri bildirim sağlanıyor.
- **Detaylı durum çubuğu**: Anlık işlemlere dair detaylı bilgiler durum çubuğunda gösteriliyor.
- **Özelleştirilebilir klavye kısayolları**: Tüm klavye kısayolları kullanıcı tarafından özelleştirilebilir.
- **Otomatik kaydetme**: Belirlenen aralıklarla otomatik kaydetme yapılabilir.

## Çıktı Formatı

Uygulama, YOLO formatında etiketler oluşturur. Her görüntü için bir metin dosyası oluşturulur ve her nesne için aşağıdaki formatta bir satır içerir:

```
<sınıf_id> <merkez_x> <merkez_y> <genişlik> <yükseklik>
```

Tüm değerler görüntü boyutuna göre normalize edilmiş (0-1 arasında) şekilde kaydedilir.

## Sorun Giderme

- **Klavye kısayolları çalışmıyor**: "Ayarlar > Klavye Kısayolları" menüsünden kısayolları kontrol edin veya varsayılana sıfırlayın.
- **Büyük görüntülerde etiketleme sorunu**: Yakınlaştırma/uzaklaştırma özelliğini kullanarak daha hassas etiketleme yapabilirsiniz.
- **Otomatik kaydetme**: "Ayarlar > Otomatik Kaydetme" menüsünden otomatik kaydetme ayarlarını yapılandırabilirsiniz.

## Katkıda Bulunma

Projeye katkıda bulunmak isterseniz lütfen bir issue açın veya pull request gönderin.

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 