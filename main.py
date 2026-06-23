import network
import ntptime 
import urequests
from machine import Pin, time_pulse_us
import time

# Konfigurasi Wi-Fi 
SSID = "Atha"
PASSWORD = "Adp123456"

# Konfigurasi Cloud IoT
BLYNK_TOKEN = "7FQeuZNg0wFwwTi34BLcMVQGVMu-zO__"

# ==========================================
# 1. KONFIGURASI PIN FISIK ESP32 (3 SLOT)
# ==========================================
# --- Pin Slot Parkir 1 ---
trig1 = Pin(5, Pin.OUT)
echo1 = Pin(18, Pin.IN)
led_merah1 = Pin(2, Pin.OUT)
led_hijau1 = Pin(4, Pin.OUT)

# --- Pin Slot Parkir 2 ---
trig2 = Pin(19, Pin.OUT)
echo2 = Pin(21, Pin.IN)
led_merah2 = Pin(12, Pin.OUT)
led_hijau2 = Pin(13, Pin.OUT)

# --- Pin Slot Parkir 3 ---
trig3 = Pin(16, Pin.OUT)
echo3 = Pin(17, Pin.IN)
led_merah3 = Pin(25, Pin.OUT) 
led_hijau3 = Pin(33, Pin.OUT)

# ==========================================
# 2. DATASET K-NN & STRUKTUR DATA REAL-TIME
# ==========================================
data_latih_jarak = [50.6, 50.5, 31.7, 16.8, 16.5, 5.5, 4.3, 3.3, 2.9, 2.3]
data_latih_label = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
JUMLAH_DATA = 10

# Penyangga Data Antrian (Circular Buffer)
buffer1 = [999.0, 999.0, 999.0]
buffer2 = [999.0, 999.0, 999.0]
buffer3 = [999.0, 999.0, 999.0]
idx1, idx2, idx3 = 0, 0, 0

# ==========================================
# 3. FUNGSI DRIVER & ALGORITMA MURNI
# ==========================================
def baca_jarak(trig_pin, echo_pin):
    trig_pin.value(0)
    time.sleep_us(2)
    trig_pin.value(1)
    time.sleep_us(10)
    trig_pin.value(0)
    try:
        durasi = time_pulse_us(echo_pin, 1, 30000)
        if durasi < 0: return 999 
        return (durasi * 0.0343) / 2
    except OSError:
        return 999

def moving_average(jarak_baru, buffer, indeks):
    buffer[indeks] = jarak_baru
    indeks = (indeks + 1) % 3
    total = 0
    for j in buffer:
        total += j
    return total / 3, indeks

def knn_klasifikasi(jarak_sensor, k=3):
    jarak_ke_titik = [0.0] * JUMLAH_DATA
    label_titik = [0] * JUMLAH_DATA
    
    for i in range(JUMLAH_DATA):
        selisih = jarak_sensor - data_latih_jarak[i]
        jarak_ke_titik[i] = selisih * selisih 
        label_titik[i] = data_latih_label[i]
        
    for i in range(JUMLAH_DATA):
        for j in range(0, JUMLAH_DATA - i - 1):
            if jarak_ke_titik[j] > jarak_ke_titik[j+1]:
                jarak_ke_titik[j], jarak_ke_titik[j+1] = jarak_ke_titik[j+1], jarak_ke_titik[j]
                label_titik[j], label_titik[j+1] = label_titik[j+1], label_titik[j]
                
    suara_0, suara_1 = 0, 0
    for i in range(k):
        if label_titik[i] == 0: suara_0 += 1
        else: suara_1 += 1
            
    return 1 if suara_1 > suara_0 else 0

# ========================================================
# HAPUS fungsi koneksi_wifi() lama, dan PASTE yang baru di sini:
# ========================================================
def koneksi_wifi():
    print("Mereset modul Wi-Fi...")
    wlan = network.WLAN(network.STA_IF)
    
    # 1. Matikan radio untuk menguras sisa memori lama
    wlan.active(False)
    time.sleep(1)
    
    # 2. Nyalakan kembali
    wlan.active(True)
    wlan.disconnect() # Putuskan paksa jika ada koneksi yang 'nyangkut'
    time.sleep(1)
    
    print(f"Mencoba terhubung ke: {SSID}")
    wlan.connect(SSID, PASSWORD)
    
    # 3. Tunggu dengan batas waktu (timeout) 20 detik
    timeout = 20
    while not wlan.isconnected() and timeout > 0:
        time.sleep(1)
        print(".", end="")
        timeout -= 1
        
    if wlan.isconnected():
        print("\nWi-Fi Terhubung Sukses!")
    else:
        print("\nGAGAL: Waktu habis. Cek kembali nama/password atau hotspot HP.")
# ========================================================

def ambil_jam_wib():
    try:
       # 1. Beri jeda napas agar aliran internet dari HP stabil dulu
        time.sleep(2) 
        
        # 2. Gunakan server waktu khusus regional Indonesia
        ntptime.host = "id.pool.ntp.org" 
        
        # 3. Ambil waktu
        ntptime.settime() 
        waktu_lokal = time.localtime(time.time() + 7 * 3600)
        jam = waktu_lokal[3] 
        menit = waktu_lokal[4]
        return jam, menit
    except Exception as e:
        # Jika masih gagal, cetak pesan error aslinya agar kita tahu penyebabnya
        print(f"Gagal sinkronisasi waktu NTP: {e}")
        return 0, 0

def prediksi_pola_kepadatan(jam):
    if 7 <= jam <= 9:
        return "TINGGI (Masuk Kuliah)"
    elif 12 <= jam <= 13:
        return "SEDANG (Istirahat)"
    elif 16 <= jam <= 17:
        return "TINGGI (Pulang Kuliah)"
    elif 18 <= jam <= 23 or 0 <= jam <= 6:
        return "LENGGANG (Malam Hari)"
    else:
        return "SEDANG (Normal)"
def kirim_ke_blynk(slot1, slot2, slot3, teks_pola, teks_sisa):
    # Mengubah spasi menjadi '%20' agar teks terbaca aman di URL internet
    teks_pola = teks_pola.replace(" ", "%20")
    teks_sisa = teks_sisa.replace(" ", "%20") 
    
    # Menambahkan V5 ke dalam URL pengiriman
    url = f"http://blynk.cloud/external/api/batch/update?token={BLYNK_TOKEN}&V1={slot1}&V2={slot2}&V3={slot3}&V4={teks_pola}&V5={teks_sisa}"
    
    # TAMBAHAN: Cetak URL ke layar agar kita bisa melihat bentuk aslinya
    print(f"-> Mencoba kirim ke Blynk: V5={teks_sisa.replace('%20', ' ')}")
    try:
        response = urequests.get(url)
        response.close()
    except OSError:
        pass

# ==========================================
# 4. LOGIKA UTAMA (BERJALAN REAL-TIME)
# ==========================================
print("Sistem Smart Parking Edge AI (3 Slot) Aktif!")

koneksi_wifi()
jam_sekarang, menit_sekarang = ambil_jam_wib()
status_pola = prediksi_pola_kepadatan(jam_sekarang)

print(f"Waktu Sistem: {jam_sekarang:02d}:{menit_sekarang:02d} WIB | Prediksi Kepadatan Nanti: {status_pola}")
print("-" * 50)

while True:
    waktu_lokal = time.localtime(time.time() + 7 * 3600) 
    jam_sekarang = waktu_lokal[3]
    menit_sekarang = waktu_lokal[4]
    
    status_pola = prediksi_pola_kepadatan(jam_sekarang)

    mentah1 = baca_jarak(trig1, echo1)
    mentah2 = baca_jarak(trig2, echo2)
    mentah3 = baca_jarak(trig3, echo3)
    
    stabil1, idx1 = moving_average(mentah1, buffer1, idx1)
    stabil2, idx2 = moving_average(mentah2, buffer2, idx2)
    stabil3, idx3 = moving_average(mentah3, buffer3, idx3)
    
    prediksi1 = knn_klasifikasi(stabil1, k=3)
    prediksi2 = knn_klasifikasi(stabil2, k=3)
    prediksi3 = knn_klasifikasi(stabil3, k=3)
    
    print(f"[{jam_sekarang:02d}:{menit_sekarang:02d} WIB | Prediksi Pola: {status_pola}]")
    print(f"Slot1: {stabil1:.1f}cm [Kelas {prediksi1}] | "
          f"Slot2: {stabil2:.1f}cm [Kelas {prediksi2}] | "
          f"Slot3: {stabil3:.1f}cm [Kelas {prediksi3}]")
    print("-" * 50)
    
    led_merah1.value(1 if prediksi1 == 1 else 0)
    led_hijau1.value(0 if prediksi1 == 1 else 1)
    
    led_merah2.value(1 if prediksi2 == 1 else 0)
    led_hijau2.value(0 if prediksi2 == 1 else 1)
    
    led_merah3.value(1 if prediksi3 == 1 else 0)
    led_hijau3.value(0 if prediksi3 == 1 else 1)
    
  # --- 5. Terjemahkan Angka menjadi Teks untuk Blynk ---
    teks_slot1 = "Terisi" if prediksi1 == 1 else "Kosong"
    teks_slot2 = "Terisi" if prediksi2 == 1 else "Kosong"
    teks_slot3 = "Terisi" if prediksi3 == 1 else "Kosong"
    
  # Menghitung jumlah slot kosong
    # Karena prediksi bernilai 1 jika Terisi dan 0 jika Kosong
    jumlah_terisi = prediksi1 + prediksi2 + prediksi3
    jumlah_kosong = 3 - jumlah_terisi
    teks_sisa = f"{jumlah_kosong} slot kosong"
    
    # --- 6. Kirim Data Teks Real-Time ke Dashboard Cloud ---
    # Masukkan teks_sisa ke dalam parameter pengiriman
    kirim_ke_blynk(teks_slot1, teks_slot2, teks_slot3, status_pola, teks_sisa)
    
    time.sleep_ms(100)
