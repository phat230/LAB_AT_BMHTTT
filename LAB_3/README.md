# LAB 3 - NHẬN DIỆN VÀ ỨNG PHÓ CÁC MỐI ĐE DỌA ĐẾN AN TOÀN THÔNG TIN

## 1. Thông tin sinh viên
- **Họ và tên:** NGUYỄN ĐỨC PHAT
- **MSSV:** 1150080152
- **Tên lab:** Lab 3 - Nhận diện và ứng phó các mối đe dọa đến an toàn thông tin

## 2. Phiên bản môi trường thực hành
- **Máy ảo:** Windows 11 Pro 25H2
- **VMware Workstation:** 26H1
- **Windows PowerShell:** 5.1
- **Microsoft Defender:** bật Real-time Protection và Tamper Protection
- **Sysmon:** 15.22
- **Autoruns:** 14.3
- **Process Explorer:** 17.14
- **Wireshark:** 4.6.8
- **Npcap:** đã cài để bắt traffic loopback
- **Python:** 3.14.7

> Lưu ý: thông tin build Windows nên ghi theo đúng ảnh chụp thực tế trong báo cáo.

## 3. Cách dựng môi trường
1. Tạo máy ảo Windows 11 bằng VMware Workstation.
2. Cấu hình Network Adapter ở chế độ **Host-only** cho phần lớn bài thực hành.
3. Tạo cấu trúc thư mục `C:\LAB3` gồm `Evidence`, `Tools`, `Downloads`, `Assets`.
4. Giải nén bộ `LAB3_Threats_Assets`.
5. Cài Python 3.14.7, Wireshark 4.6.8 và Npcap.
6. Tải Sysmon, Autoruns và Process Explorer của Microsoft Sysinternals.
7. Kiểm tra Defender, Firewall, hệ điều hành, network và process để tạo baseline.
8. Khi thực hiện HTTPS, tạm chuyển VM sang **NAT** để có Internet, sau đó chuyển lại **Host-only**.

## 4. Các tình huống đã thực hiện

### TH1 - Xác định tài sản, lỗ hổng, mối đe dọa và rủi ro
- Tạo `risk_register.csv`.
- Phân loại 5 tình huống theo các nhóm: hành động vô ý, hành động cố ý, thảm họa/sự cố môi trường, lỗi kỹ thuật và lỗi quản lý.

**Kết quả:** PASS

### TH2 - Kiểm chứng Microsoft Defender bằng EICAR
- Tạo chuỗi kiểm thử EICAR.
- Microsoft Defender phát hiện `Virus:DOS/EICAR_Test_File`.
- Trạng thái xử lý: `Quarantined`.
- Không tắt Defender và không tạo exclusion.

**Kết quả:** PASS

### TH3 - Tấn công mật khẩu và nguy cơ keylogging
- Tạo tài khoản thử nghiệm `lab3user`.
- Bật Audit Logon Success/Failure.
- Tạo đăng nhập đúng và sai có kiểm soát.
- Thu các Event ID `4624`, `4625`, `4648`.
- Đổi mật khẩu và kiểm tra mật khẩu cũ không còn sử dụng được.

**Kết quả:** PASS

### TH4 - Persistence và dịch vụ lắng nghe
- Cài Sysmon và kiểm tra Event ID 1.
- Tạo persistence lành tính `LAB3_Run_Demo` và `LAB3_Persistence_Demo`.
- Kiểm tra bằng Sysmon, Autoruns và Process Explorer.
- Tạo HTTP server chỉ lắng nghe tại `127.0.0.1:8080`.
- Đối chiếu PID của `python.exe` bằng `Get-NetTCPConnection` và Process Explorer.

**Kết quả:** PASS

### TH5 - HTTP so với HTTPS/TLS
- Bắt HTTP loopback bằng Wireshark.
- Với HTTP, đọc được Request URI có chuỗi `TRAINING_ONLY`.
- Với HTTPS/TLS tới `example.com`, chỉ quan sát được metadata/handshake, không đọc trực tiếp Request URI.
- Không thực hiện ARP poisoning, DNS spoofing, fake Wi-Fi, session hijacking hoặc chèn chứng chỉ.

**Kết quả:** PASS

### TH6 - DoS, DDoS và Mail Bombing
Local load test thực tế:
```text
target=http://127.0.0.1:8080/
requests=50 workers=5
ok=50 failures=0
```

- Phân tích `ddos_sample.csv` và thấy nhiều `SourceIP` khác nhau.
- Phân tích `mailbomb_sample.csv`.
- Sender bất thường: `bulk-sender@example.invalid` với 60 email.
- Tổng số bản ghi: 80.
- Tổng dung lượng: 781390 bytes.

**Kết quả:** PASS

### TH7 - Social Engineering, Phishing và Spear Phishing
- Phân tích `phishing_email.txt`.
- Nhận diện các dấu hiệu: khẩn cấp, display name đáng tin giả, domain cần xác minh, `Reply-To` khác `From`, yêu cầu link/credential.
- Phân loại 6 nhóm: Phishing, Spear Phishing, Watering Hole, Pretexting, Baiting, Quid Pro Quo.

**Kết quả:** PASS

## 5. Cleanup và kiểm tra sau thực hành
- Xóa `LAB3_Run_Demo`.
- Xóa Scheduled Task `LAB3_Persistence_Demo`.
- Dừng HTTP server tại port `8080`.
- Xóa tài khoản `lab3user`.
- Kiểm tra Defender vẫn bật.
- Thu `autoruns_after.csv`.
- So sánh `autoruns_before.csv` và `autoruns_after.csv`.
- Tạo `evidence_sha256.csv`.

**Kết quả:** PASS

## 6. Lỗi gặp phải và cách khắc phục

### Lỗi 1 - Sai đường dẫn `lab3_assets`
Sau khi giải nén, thư mục bị lồng nhiều cấp.

**Cách khắc phục:**
```powershell
Get-ChildItem C:\LAB3 -Recurse -Filter sysmon-lab.xml
```
Sau đó đưa `lab3_assets` về đúng `C:\LAB3\lab3_assets`.

### Lỗi 2 - PowerShell xuất hiện dấu `>>`
PowerShell đang chờ kết thúc câu lệnh nhiều dòng.

**Cách khắc phục:** nhấn `Ctrl + C` và chạy lại lệnh trên một dòng.

### Lỗi 3 - Python đã cài nhưng lệnh `python` chưa nhận
Python chưa nằm trong PATH.

**Cách khắc phục:** bổ sung đường dẫn Python vào PATH và kiểm tra:
```powershell
python --version
```

### Lỗi 4 - `auditpol` báo `Error 0x00000057`
GUID subcategory chưa được đặt trong dấu ngoặc kép.

**Cách khắc phục:**
```powershell
auditpol /set /subcategory:"{0CCE9215-69AE-11D9-BED3-505054503030}" /success:enable /failure:enable
```

### Lỗi 5 - `runas` không chạy
Đã kiểm tra/reset mật khẩu `lab3user`, kiểm tra dịch vụ Secondary Logon và dùng:
```powershell
runas.exe /user:"$env:COMPUTERNAME\lab3user" cmd.exe
```

### Lỗi 6 - Wireshark không thấy interface mạng
Nguyên nhân là Npcap chưa được cài.

**Cách khắc phục:** cài lại Wireshark 4.6.8 ở chế độ interactive, cài Npcap và kiểm tra:
```powershell
& "C:\Program Files\Wireshark\tshark.exe" -D
```
Sau đó xuất hiện `Adapter for loopback traffic capture`.

### Lỗi 7 - Winget không tải được khi VM dùng Host-only
VM không có Internet/DNS khi cài lại Wireshark.

**Cách khắc phục:** tạm chuyển Network Adapter sang **NAT**, cài Wireshark/Npcap xong rồi chuyển lại **Host-only**.

## 7. Evidence chính
```text
auth_events_before_rotation.txt
autoruns_before.csv
autoruns_after.csv
autoruns_diff.txt
baseline_defender.txt
baseline_firewall.txt
baseline_network.txt
baseline_os.txt
baseline_processes.txt
ddos_sources.txt
defender_eicar.txt
local_load_test.txt
mail_sender_counts.txt
mail_volume.txt
risk_register.csv
sysmon_persistence.txt
task_ran.txt
threat_classification.csv
evidence_sha256.csv
```

## 8. Kết luận
Qua LAB3, em đã thực hành nhận diện và phân tích malware, tấn công mật khẩu, persistence/backdoor, sniffing, DoS/DDoS, mail bombing và social engineering. Em sử dụng Microsoft Defender, Sysmon, Autoruns, Process Explorer và Wireshark để thu thập và đối chiếu bằng chứng.

Các tình huống được thực hiện trong phạm vi máy ảo và localhost. Không thực hiện DDoS, mail bombing, spoofing hoặc MITM chủ động ra hệ thống bên ngoài.
