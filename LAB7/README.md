# LAB 7 – pfSense Web Protection: Squid, E2Guardian, ClamAV và Web Filtering

## Thông tin sinh viên

- **Họ tên:** Nguyễn Đức Phát
- **MSSV:** 1150080152
- **Lớp:** 11-ĐH-THMT
- **Tên lab:** LAB 7 – pfSense Web Protection (Firewall + Explicit Proxy + Content Filtering)
- **Nền tảng:** VMware Workstation Pro 17

> **Phạm vi:** Môi trường máy ảo phục vụ thực hành; các domain `*.lab7.test` là website mô phỏng nội bộ. README ghi trạng thái theo những kết quả đã kiểm thử, không xem hình minh họa/mô phỏng là minh chứng hoàn thành.

## 1. Môi trường thực hành

- **pfSense** (kế thừa LAB 6): quản lý các mạng WAN, LAN, MGMT, DMZ và luật firewall.
- **Windows Server 2022 / DC01:** Active Directory và DNS nội bộ cho `lab7.test`.
- **Windows Client-A / Client-B:** thử chính sách truy cập web.
- **Ubuntu WEB-PROXY:** chạy Squid, E2Guardian và ClamAV.
- **Ubuntu DMZ-WEB:** Nginx phục vụ các website mô phỏng.

### Địa chỉ mạng chính

| Thành phần | IP / mạng | Vai trò |
|---|---|---|
| pfSense LAN | `10.6.0.1/24` | Gateway cho Client và WEB-PROXY |
| pfSense MGMT | `192.168.56.254/24` | Quản trị WebGUI |
| pfSense DMZ | `172.16.6.1/24` | Gateway DMZ |
| DC01 | `10.6.0.10` | AD/DNS cho `lab7.test` |
| Client-A | `10.6.0.21` | Máy kiểm thử A |
| Client-B | `10.6.0.22` | Máy kiểm thử B |
| WEB-PROXY | `10.6.0.30` | E2Guardian `:8080` → Squid `127.0.0.1:3128` |
| DMZ-WEB | `172.16.6.10` | Nginx; nhiều site định danh bằng Host header |

### Luồng truy cập web

```text
Client-A / Client-B (10.6.0.21 / 10.6.0.22)
       |
       | Explicit HTTP proxy :8080
       v
WEB-PROXY (10.6.0.30)
       | E2Guardian :8080 (policy, cảnh báo, lọc nội dung)
       v
Squid 127.0.0.1:3128 (upstream proxy)
       |
       v
pfSense -> DMZ-WEB (172.16.6.10, Nginx, *.lab7.test)
```

## 2. Cách dựng môi trường

### WEB-PROXY

- Tạo Ubuntu Server cho WEB-PROXY, đặt IP `10.6.0.30` trong LAN của pfSense.
- Cài và cấu hình Squid, E2Guardian, ClamAV.
- Cấu hình Squid chỉ lắng nghe `127.0.0.1:3128`, client **không** truy cập Squid trực tiếp.
- Client dùng proxy `10.6.0.30:8080` (E2Guardian).

Các lệnh kiểm tra đã dùng trên WEB-PROXY:

```bash
ip -br addr
sudo systemctl status squid --no-pager
sudo systemctl status e2guardian --no-pager
sudo systemctl status clamav-daemon --no-pager
sudo ss -ltnp | grep -E ':8080|:3128'
```

### DMZ-WEB và DNS nội bộ

- Dùng lại DMZ-WEB, tạo các trang Nginx cho `*.lab7.test`.
- DNS trên DC01 định hướng các domain thử nghiệm tới DMZ-WEB.
- Trong quá trình dựng, đã sử dụng script `setup_lab7_dmz_web.sh` và xác minh bằng `curl` với Host header.

```bash
# Chạy trên DMZ-WEB (khi đã có script đúng đường dẫn)
sudo bash /tmp/setup_lab7_dmz_web.sh
curl -H 'Host: jobs.lab7.test' http://127.0.0.1/
```

### Kiểm thử HTTP qua proxy

```bash
# Chạy trên WEB-PROXY hoặc Client có curl
curl -i --max-time 15 -x http://10.6.0.30:8080 http://normal.lab7.test
curl -i --max-time 15 -x http://10.6.0.30:8080 http://jobs.lab7.test
curl -i --max-time 15 -x http://10.6.0.30:8080 http://weapons.lab7.test
```

`normal.lab7.test` đã từng trả HTTP `200 OK` qua proxy. Việc truy cập trực tiếp có lần bị redirect `302` đến Captive Portal; **redirect này không tự chứng minh** firewall đã DROP mọi kết nối TCP/80,443 không đi qua proxy.

## 3. Alias và Firewall Rules trên pfSense

### Alias

| Alias | Loại | Giá trị |
|---|---|---|
| `LAB7_CLIENTS` | Host | `10.6.0.21`, `10.6.0.22` |
| `LAB7_PROXY` | Host | `10.6.0.30` |
| `WEB_PORTS` | Port | `80`, `443` |
| `MAIL_PORTS` | Port | `25`, `465`, `587`, `110`, `995`, `143`, `993` |

### Chính sách firewall mục tiêu

| Thứ tự logic | Action | Source | Destination / port | Mục đích |
|---|---|---|---|---|
| 1 | Pass | LAN | DC01 – TCP/UDP 53 | DNS nội bộ |
| 2 | Pass | `LAB7_CLIENTS` | `LAB7_PROXY` – TCP 8080 | Client dùng proxy |
| 3 | Pass | LAN | `MAIL_PORTS` | Cho email theo bài lab |
| 4 | Block | `LAB7_CLIENTS` | Any – TCP 80/443 | Chống truy cập web trực tiếp |
| 5 | Pass | `LAB7_PROXY` | Web cần thiết | Proxy truy cập web/DMZ |
| 6 | Block | LAN | Any (còn lại) | Cô lập theo chính sách |

**Lưu ý:** Bảng mô tả thiết kế của bài; thứ tự thực tế còn phụ thuộc các rule có sẵn trên pfSense. Ảnh đã ghi lại rule `LAB7 Allow Clients to Proxy` với source `LAB7_CLIENTS`, destination `LAB7_PROXY`, TCP 8080.

## 4. Cấu hình chính sách E2Guardian

### Danh sách domain thực hành

| Nhóm / domain | Policy mong muốn |
|---|---|
| `normal.lab7.test` | Allow |
| `education.lab7.test` | Allow / exception |
| `download.lab7.test` | Nguồn file kiểm thử |
| `china.lab7.test`, `mideast.lab7.test` | Geo-Sim hard block |
| `jobs.lab7.test` | Job Search hard block |
| `blockedgame.lab7.test` | Specific Game hard block |
| `weapons.lab7.test`, `politics.lab7.test`, `religion.lab7.test` | Warning / temporary bypass |
| `streaming.lab7.test` | Warning |
| `entertainment.lab7.test`, `games.lab7.test` | Lịch truy cập 60 phút (mô phỏng) |

Đã thao tác với các file danh sách:

```text
/etc/e2guardian/lists/bannedsitelist
/etc/e2guardian/lists/exceptionsitelist
/etc/e2guardian/lists/lab7_ent_allow
/etc/e2guardian/e2guardianf1.conf
```

Các lệnh kiểm tra nhanh:

```bash
sudo grep -nF 'lab7.test' /etc/e2guardian/lists/bannedsitelist
sudo tail -n 10 /etc/e2guardian/lists/exceptionsitelist
sudo grep -n 'lab7_ent_allow' /etc/e2guardian/e2guardianf1.conf
sudo systemctl restart e2guardian
sudo systemctl is-active e2guardian
```

**Điểm cần phân biệt:** Danh sách cấm đã chứa các domain được yêu cầu, nhưng với `jobs.lab7.test`, trang cảnh báo từng hiện **Acknowledge** và người thực hiện vẫn vào được Jobs Site. Do đó **chưa thể ghi mục Job Search hard block là PASS**. `weapons.lab7.test` đã hiển thị trang block/warning và có thử nghiệm bypass.

## 5. Các tình huống đã thực hiện

| Tình huống | Kết quả theo các lần thực hành |
|---|---|
| Squid và E2Guardian khởi động, proxy port 8080 | **ĐÃ KIỂM TRA** |
| `normal.lab7.test` qua proxy | **PASS – HTTP 200** |
| Website mô phỏng trên DMZ-WEB | **PASS – Nginx trả nội dung đúng Host** |
| `jobs.lab7.test` hiển thị trang chặn/cảnh báo | **PASS ở mức hiển thị block page**, nhưng **chưa đạt hard block** vì có Acknowledge |
| `weapons.lab7.test` hiển thị block/warning | **ĐÃ KIỂM TRA**, từng có bypass |
| `education.lab7.test` trong danh sách allow | **ĐÃ CẤU HÌNH/THỬ NGHIỆM**, cần giữ ảnh truy cập không cảnh báo |
| Danh sách Geo-Sim, game, streaming | **ĐÃ THÊM DOMAIN**, chưa đủ ảnh kiểm tra từng policy hoàn chỉnh |
| EICAR qua HTTP | **ĐÃ ĐƯỢC NGƯỜI THỰC HIỆN XÁC NHẬN BỊ CHẶN**; nên bổ sung log scanner |
| Schedule Entertainment/Game 60 phút | **CHƯA XÁC MINH ĐẠT** cả trong và ngoài khung giờ |
| Direct HTTP/HTTPS bị block khi tắt proxy | **CHƯA CÓ MINH CHỨNG DROP CHẮC CHẮN** (từng nhận Captive Portal 302) |
| Chặn tải file trên 100 MB | **CHƯA THỰC HIỆN/CHƯA XÁC MINH** |
| Tùy chỉnh block page | **CHƯA TRIỂN KHAI ĐƯỢC KIỂM CHỨNG** |
| HTTPS inspection / SSL MITM | **KHÔNG THỰC HIỆN** (phần mở rộng) |

> Hình ghi nhãn `MÔ PHỎNG` trong những bản tài liệu trước chỉ là minh họa kết quả dự kiến, **không dùng làm bằng chứng thực tế**.

## 6. Kết quả chính và lệnh trình diễn

```bash
# Trên Client hoặc WEB-PROXY: kiểm thử site hợp lệ và site cảnh báo
curl -I --max-time 15 -x http://10.6.0.30:8080 http://normal.lab7.test
curl -i --max-time 15 -x http://10.6.0.30:8080 http://jobs.lab7.test
curl -i --max-time 15 -x http://10.6.0.30:8080 http://weapons.lab7.test

# Trên WEB-PROXY: theo dõi log lọc web / proxy
sudo tail -n 30 /var/log/e2guardian/access.log
sudo tail -n 30 /var/log/squid/access.log
sudo journalctl -u clamav-daemon -n 30 --no-pager

# EICAR (file thử nghiệm an toàn, không phải malware thật)
curl -i --max-time 30 -x http://10.6.0.30:8080 \
  http://download.lab7.test/files/eicar.com.txt
```

Các mục đã chứng minh được: kết nối proxy, trang mô phỏng Nginx, các trang block/warning và log E2Guardian; thử nghiệm EICAR được xác nhận đã chặn trong quá trình làm bài. Các mục nâng cao chưa kiểm thử đầy đủ được ghi riêng trong bảng kết quả.

## 7. Lỗi gặp phải và cách khắc phục

### Domain Jobs chưa bị hard block
- **Hiện tượng:** `jobs.lab7.test` hiện trang chặn nhưng có nút Acknowledge, sau đó mở được website.
- **Xử lý:** rà soát `bannedsitelist`, chính sách `bannedbypass`/exception và luật E2Guardian tương ứng; kiểm thử lại không có bypass trước khi đánh dấu PASS.

### Tắt proxy nhưng nhận trang Captive Portal
- **Hiện tượng:** HTTP trả `302 Found` tới WebGUI/Captive Portal.
- **Ý nghĩa:** Có chuyển hướng xác thực; chưa đủ để khẳng định direct traffic bị firewall DROP.
- **Xử lý:** xem thứ tự rule pfSense, bật logging, thử TCP/80 và TCP/443 khi không cấu hình proxy.

### EICAR ban đầu trả HTTP 200
- **Hiện tượng:** Nginx từng trả file EICAR nguyên bản.
- **Xử lý:** cấu hình E2Guardian content scanner/ClamAV, restart dịch vụ, thử lại; người thực hiện xác nhận EICAR đã bị chặn.

### Lỗi quét nội dung tại trang Games
- **Hiện tượng:** `Could not perform content scan`.
- **Ý nghĩa:** Lỗi scanner không phải bằng chứng schedule 60 phút hoạt động đúng.

### Nhầm tên lệnh/thư mục
- **Hiện tượng:** `systemctl` gõ sai thành `systmctl`, `nano` gõ sai hoặc sai file danh sách E2Guardian.
- **Xử lý:** dùng đường dẫn đúng dưới `/etc/e2guardian/`, kiểm tra với `ls`, `grep`, `systemctl`.

## 8. Ảnh minh chứng và file nộp

Các ảnh nên lưu trong thư mục `images/` của LAB 7, với nội dung:

1. Topology/VM và IP WEB-PROXY.
2. Alias và rule cho phép Client đến proxy `:8080`.
3. Truy cập `normal.lab7.test` qua proxy – HTTP 200.
4. Danh sách domain bị cấm và trang warning/block.
5. Log E2Guardian, Squid, ClamAV và Firewall.
6. EICAR bị scanner chặn (nếu có log/ảnh thực tế).
7. Các mục còn thiếu chỉ bổ sung khi chạy và chụp được kết quả thật.

Cấu trúc GitHub đề xuất:

```text
LAB7/
├── README.md
├── images/                   # Ảnh chụp thực tế
├── commands.md               # Lệnh thực hành nếu cần
└── configs/                   # Chỉ lưu bản đã loại bỏ thông tin nhạy cảm
```

Xuất cấu hình pfSense tại **Diagnostics → Backup & Restore**. **Không đẩy bản `config.xml` chứa mật khẩu, khóa, secret, thông tin đăng nhập hoặc chứng chỉ riêng tư lên GitHub công khai.**

## 9. Kết luận

LAB 7 đã dựng được mô hình **pfSense → E2Guardian → Squid → Nginx**, thử truy cập website bình thường, chặn/cảnh báo theo danh sách và ghi log. Phần hard block không bypass, kiểm thử chính sách 60 phút, giới hạn 100 MB và tùy chỉnh block page cần minh chứng hoặc hoàn thiện bổ sung. HTTPS inspection là phần mở rộng chưa thực hiện.
