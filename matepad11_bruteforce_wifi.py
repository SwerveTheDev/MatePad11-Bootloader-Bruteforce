#!/usr/bin/env python3
import subprocess
import time
import os
import random

# Cihazın fastboot modunda olduğundan emin ol
print("Cihazınızı fastboot moduna alın: Güç + Ses Kısma tuşuna basılı tutun.")
input("Cihaz hazır olduğunda Enter'a basın...")

# Seri numarasını al (opsiyonel, yoksa rastgele bir başlangıç kullanılır)
serial_input = input("Cihazınızın seri numarasını girin (bilmiyorsanız '0' yazın): ")
if serial_input == "0":
    base_seed = int(time.time() * 1000)  # Rastgele bir başlangıç için zaman damgası
else:
    base_seed = int(''.join(filter(str.isdigit, serial_input)))  # Seri numarasından sayısal değer

# Bruteforce parametreleri
start_code = 1000000000000000  # 16 haneli başlangıç kodu
increment = random.randint(100, 1000) * base_seed % 9999  # Rastgele ama tutarlı bir artış
max_attempts_before_reboot = 5  # HarmonyOS 3.0’da 5 deneme limiti
save_interval = 100  # Her 100 denemede bir kaydet

# Dosya ayarları
progress_file = "matepad11_progress.txt"
unlock_file = "matepad11_unlock_code.txt"

def bruteforce_bootloader(start, increment):
    current_code = start
    attempt_count = 0
    reboot_count = 0

    while True:
        code_str = str(current_code).zfill(16)  # 16 hane için sıfır ekle
        progress = round((current_code / 10000000000000000) * 100, 4)
        print(f"Denenen kod: {code_str} | İlerleme: {progress}% | Deneme: {attempt_count}")

        # Fastboot ile kilit açma komutu
        result = subprocess.run(f"fastboot oem unlock {code_str}", 
                                shell=True, 
                                capture_output=True, 
                                text=True)
        output = result.stderr.lower()

        # Çıktıyı analiz et
        if "success" in output or "unlocked" in output:
            print(f"BAŞARILI! Bootloader kodu: {code_str}")
            with open(unlock_file, "w") as f:
                f.write(f"Bootloader kodu: {code_str}\nDeneme sayısı: {attempt_count}")
            return code_str
        elif "failed" in output or "invalid" in output:
            print("Kod yanlış, devam ediliyor...")
        elif "reboot" in output or "locked" in output:
            print("Cihaz kilitlendi, yeniden başlatılıyor...")
            os.system("fastboot reboot-bootloader")
            time.sleep(10)  # Yeniden başlatma için bekle
            reboot_count += 1
        else:
            print(f"Bilinmeyen yanıt: {output}")
            break

        attempt_count += 1

        # HarmonyOS 3.0 koruması: 5 denemede bir yeniden başlat
        if attempt_count % max_attempts_before_reboot == 0:
            print("5 deneme sınırı aşıldı, fastboot yeniden başlatılıyor...")
            os.system("fastboot reboot-bootloader")
            time.sleep(10)

        # İlerlemeyi kaydet
        if attempt_count % save_interval == 0:
            with open(progress_file, "w") as f:
                f.write(f"Son denenen kod: {code_str}\nDeneme sayısı: {attempt_count}")

        current_code += increment

# ADB ve fastboot ortamını hazırla
print("ADB ve Fastboot kontrol ediliyor...")
subprocess.run("adb devices", shell=True)
print("Cihazda USB hata ayıklamayı açın ve izni onaylayın.")

# Seri numarasını fastboot’tan al (isteğe bağlı kontrol)
serial_check = subprocess.run("fastboot getvar serialno", shell=True, capture_output=True, text=True)
if serial_check.stdout:
    print(f"Cihaz seri numarası: {serial_check.stdout.strip()}")

# Cihazı fastboot moduna al
os.system("adb reboot bootloader")
time.sleep(10)

# Bruteforce’u başlat
print("Bruteforce başlıyor...")
unlock_code = bruteforce_bootloader(start_code, increment)

# Sonuç kontrolü
if unlock_code:
    print(f"Bootloader kilidi açıldı! Kod: {unlock_code}")
    os.system("fastboot getvar unlocked")
else:
    print("Bruteforce başarısız oldu veya manuel olarak durduruldu.")
