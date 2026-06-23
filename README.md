# Sistem Smart Parking Berbasis Edge AI (k-NN) dan IoT

Proyek ini adalah purwarupa sistem parkir pintar yang menggunakan mikrokontroler ESP32. Sistem ini menerapkan **Edge AI** menggunakan algoritma **K-Nearest Neighbors (k-NN)** murni (ditulis *from scratch* tanpa library eksternal) untuk mengklasifikasikan status slot parkir (Kosong/Terisi) berdasarkan pembacaan jarak dari sensor ultrasonik. Hasil klasifikasi dikirim secara *real-time* ke *dashboard* **Blynk IoT**.

## 🛠️ Komponen Perangkat Keras
1. 1x Mikrokontroler ESP32 (NodeMCU)
2. 3x Sensor Ultrasonik HC-SR04
3. 3x LED Merah (Indikator Terisi) & 3x LED Hijau (Indikator Kosong)
4. Kabel Jumper dan Breadboard

## 📌 Konfigurasi Pin (Wiring)
* **Slot 1:** Trig (Pin 5), Echo (Pin 18), LED Merah (Pin 2), LED Hijau (Pin 4)
* **Slot 2:** Trig (Pin 19), Echo (Pin 21), LED Merah (Pin 12), LED Hijau (Pin 13)
* **Slot 3:** Trig (Pin 16), Echo (Pin 17), LED Merah (Pin 25), LED Hijau (Pin 33)

## 🚀 Cara Menjalankan Sistem
1. Pastikan komputer telah terinstal **Thonny IDE** dan ESP32 telah di-*flash* dengan firmware **MicroPython**.
2. Unduh file `main.py` dari repositori ini.
3. Buka file `main.py` menggunakan Thonny IDE.
4. Sesuaikan konfigurasi jaringan pada baris berikut dengan Wi-Fi Anda:
   ```python
   SSID = "Nama_WiFi_Anda"
   PASSWORD = "Password_WiFi_Anda"
