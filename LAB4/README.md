# LAB 4 – KHẢO SÁT VÀ ĐÁNH GIÁ BỀ MẶT MẠNG BẰNG NMAP

## 1. Thông tin sinh viên

- Họ và tên: Nguyễn Đức Phát
- MSSV: 1150080152
- Lớp: 11-ĐH-THMT
- Môn học: An Toàn và Bảo mật hệ thống thông tin

## 2. Môi trường thực hành

- VMware Workstation Pro 17
- Ubuntu 26.04.1 LTS
- Nmap 7.98
- Metasploitable 2
- Kiểu mạng: Host-Only
- Ubuntu Scanner: 192.168.56.128/24
- Metasploitable 2: 192.168.56.130/24
- Dải mạng thực hành: 192.168.56.0/24

## 3. Cách dựng môi trường

1. Tạo máy ảo Ubuntu trên VMware Workstation.
2. Tạo hoặc import máy ảo Metasploitable 2.
3. Đặt cả hai máy ảo vào cùng mạng Host-Only.
4. Kiểm tra địa chỉ IP của Ubuntu bằng:
   ip -br addr
5. Kiểm tra địa chỉ IP của Metasploitable bằng:
   ifconfig
6. Kiểm tra kết nối giữa hai máy.
7. Sử dụng Ubuntu làm máy quét và Metasploitable 2 làm máy mục tiêu.

## 4. Các tình huống đã thực hiện

### 4.1 Host Discovery

Lệnh:

sudo nmap -sn 192.168.56.0/24

Kết quả:

- Phát hiện các host đang hoạt động trong mạng Host-Only.
- Metasploitable 2 được xác định tại 192.168.56.130.

Trạng thái: PASS

### 4.2 TCP Connect Scan

Lệnh:

nmap -sT 192.168.56.130

Kết quả:

- Phát hiện 23 cổng TCP mở.
- 977 cổng ở trạng thái closed.

Trạng thái: PASS

### 4.3 SYN Scan

Lệnh:

sudo nmap -sS 192.168.56.130

Kết quả:

- Phát hiện 23 cổng mở.
- Kết quả tương đồng với TCP Connect Scan.

Trạng thái: PASS

### 4.4 FIN, Xmas và NULL Scan

sudo nmap -sF 192.168.56.130
sudo nmap -sX 192.168.56.130
sudo nmap -sN 192.168.56.130

Kết quả:

- Một số cổng được Nmap xác định ở trạng thái open|filtered.
- Không coi open|filtered là bằng chứng chắc chắn cổng đang mở.

Trạng thái: PASS

### 4.5 ACK Scan

sudo nmap -sA 192.168.56.130

Kết quả:

- 1000 cổng được xác định là unfiltered trong phép kiểm tra này.

Trạng thái: PASS

### 4.6 UDP Scan

sudo nmap -sU --top-ports 20 192.168.56.130

Kết quả tiêu biểu:

- 53/udp open domain
- 137/udp open netbios-ns
- Một số cổng ở trạng thái open|filtered.

Trạng thái: PASS

### 4.7 Phát hiện dịch vụ và phiên bản

sudo nmap -sV 192.168.56.130

Một số dịch vụ phát hiện được:

- FTP: vsftpd 2.3.4
- SSH: OpenSSH 4.7p1
- HTTP: Apache 2.2.8
- SMB: Samba
- FTP port 2121: ProFTPD 1.3.1
- MySQL 5.0.51a
- PostgreSQL 8.3.x
- VNC
- UnrealIRCd
- Apache Tomcat

Trạng thái: PASS

### 4.8 OS Detection

sudo nmap -O 192.168.56.130
sudo nmap -A 192.168.56.130

Kết quả:

- Hệ điều hành được nhận dạng thuộc Linux 2.6.x.
- Network distance: 1 hop.

Trạng thái: PASS

### 4.9 NSE – SMB OS Discovery

sudo nmap -p 445 --script smb-os-discovery 192.168.56.130

Kết quả:

- OS: Unix
- Samba 3.0.20-Debian
- Computer name: metasploitable
- Domain: localdomain

Trạng thái: PASS

### 4.10 NSE – MS17-010

sudo nmap -p 445 --script smb-vuln-ms17-010 192.168.56.130

Kết quả:

- Script không trả về trạng thái VULNERABLE.
- Không đủ bằng chứng để kết luận hệ thống có hoặc không có MS17-010.

Trạng thái: PASS

### 4.11 Lưu kết quả

sudo nmap -sV -O 192.168.56.130 -oN ket_qua.txt
sudo nmap -sV -O 192.168.56.130 -oX ket_qua.xml
sudo nmap -p 445 192.168.56.0/24 -oG smb.txt

Kết quả:

- Tạo được các file output phục vụ báo cáo.

Trạng thái: PASS

### 4.12 Hardening dịch vụ FTP

Trước khi hardening:

sudo nmap -sV -p 2121 192.168.56.130 -oN before_ftp.txt

Kết quả:

- 2121/tcp open
- ProFTPD 1.3.1

Trên Metasploitable:

sudo /etc/init.d/proftpd stop

Sau khi hardening:

sudo nmap -sV -p 2121 192.168.56.130 -oN after_ftp.txt

Kết quả:

- Port 2121 chuyển từ open sang closed.
- Bề mặt tấn công được giảm do dịch vụ không cần thiết đã được dừng.

Sau khi hoàn thành thử nghiệm, dịch vụ được khôi phục:

sudo /etc/init.d/proftpd start

Trạng thái: PASS

## 5. Lỗi gặp phải và cách khắc phục

### Lỗi 1: Không có kết nối Internet trong Host-Only

Nguyên nhân:

- Host-Only chỉ phục vụ mạng nội bộ giữa các máy ảo.

Khắc phục:

- Tạm thời chuyển Ubuntu sang NAT để cài xsltproc.
- Sau khi cài xong chuyển lại Host-Only.

### Lỗi 2: Chạy lệnh ProFTPD trên Ubuntu

Lỗi:

sudo: /etc/init.d/proftpd: command not found

Nguyên nhân:

- ProFTPD cần được stop/start trên máy Metasploitable 2, không phải Ubuntu scanner.

Khắc phục:

- Chuyển sang Metasploitable và chạy:

sudo /etc/init.d/proftpd stop

### Lỗi 3: Nhầm -O với -0

Khắc phục:

- -O: chữ O hoa, dùng để OS Detection.
- -oN: lưu Normal Output.
- -oX: lưu XML.
- -oG: lưu Grepable Output.

## 6. Kết luận

LAB4 đã thực hiện thành công việc phát hiện host, quét TCP/UDP,
xác định dịch vụ và phiên bản, nhận dạng hệ điều hành, sử dụng NSE,
lưu kết quả quét và thực hiện hardening dịch vụ ProFTPD.

Kết quả trước và sau hardening cho thấy việc tắt dịch vụ không cần thiết
giúp giảm bề mặt tấn công của hệ thống.
