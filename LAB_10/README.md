# LAB 10 – Remote DNS Cache Poisoning & Kaminsky Attack Simulation

## Thông tin sinh viên

- **Họ và tên:** Nguyễn Đức Phát
- **MSSV:** 1150080152
- **Lớp:** 11-ĐH-THMT
- **Tên bài lab:** LAB 10 – Remote DNS Cache Poisoning (Kaminsky Simulation) qua pfSense Router
- **Nền tảng:** VMware Workstation Pro 17

> **Tuyên bố an toàn:** Toàn bộ quá trình thực nghiệm tấn công đầu độc bộ nhớ đệm DNS (Kaminsky DNS Cache Poisoning) chỉ được tiến hành trong môi trường mạng ảo hóa khép kín (Host-Only / LAN Segments) với miền thử nghiệm cục bộ `.test` (RFC 2606) và dải địa chỉ IP riêng biệt (RFC 1918) do tường lửa pfSense định tuyến và kiểm soát. Tuyệt đối không gửi gói tin bất hợp pháp ra môi trường mạng internet thực tế.

---

## 1. Mục tiêu bài lab

Bài thực hành LAB 10 tập trung nghiên cứu, mô phỏng và phòng thủ phương thức tấn công kinh điển **Kaminsky DNS Cache Poisoning**, trả lời trọn vẹn 5 mục tiêu cốt lõi:

### 1.1. Phân biệt sự khác nhau giữa Local DNS Spoofing và Remote DNS Cache Poisoning (Kaminsky)
* **Local DNS Spoofing (LAB 8):** Kẻ tấn công nằm **cùng một mạng LAN/broadcast domain** với nạn nhân hoặc DNS Resolver. Kẻ tấn công có thể dễ dàng nghe lén (Sniff) gói tin DNS Query truyền trên mạng, đọc trực tiếp 16-bit **Transaction ID (TXID)** và cổng nguồn **UDP Source Port**, sau đó lập tức chèn gói tin DNS Reply giả mạo (Race Condition).
* **Remote DNS Cache Poisoning / Kaminsky (LAB 10):** Kẻ tấn công ở một mạng hoàn toàn **khác (Remote / Off-path)** qua Router/Tường lửa pfSense. Kẻ tấn công **không thể bắt được gói tin** của Resolver, không biết trước TXID và cổng nguồn. Hơn nữa, phương pháp cổ điển nếu đoán sai sẽ làm Resolver lưu kết quả hợp lệ vào Cache suốt thời gian TTL (khiến kẻ tấn công phải đợi hàng giờ đến hàng ngày). **Kỹ thuật Kaminsky giải quyết vấn đề này** bằng cách truy vấn liên tục các tên miền con ngẫu nhiên không tồn tại (Random Non-existent Subdomains như `rand123.example.lab10.test`). Cache không bị khóa, và kẻ tấn công chèn bản ghi **NS (Name Server) ủy quyền** kèm **Glue Record** trong Authority/Additional Section, từ đó **chiếm quyền kiểm soát toàn bộ domain** vĩnh viễn chỉ sau một lần đoán trúng.

### 1.2. Cô lập ATTACKER khỏi DNS-LAB bằng tường lửa pfSense
* ATTACKER (Kali) được đưa sang mạng riêng **ATTACKNET (`10.10.0.0/24`)**, trong khi DNS-SERVER và VICTIM nằm ở **DNSLAB (`10.9.0.0/24`)**.
* pfSense hoạt động như một Gateway/Firewall định tuyến Layer 3: pfSense **chặn hoàn toàn lưu lượng Broadcast/Promiscuous** giữa hai mạng.
* Kiểm chứng thực tế: Khi chạy `tcpdump` trên Kali trong lúc VICTIM truy vấn DNS, số gói tin bắt được là **0 packets** (chứng minh tính năng Remote Off-path tuyệt đối).

### 1.3. Phân tích vai trò của TXID, UDP Source Port, Cache TTL và bản ghi NS
* **Transaction ID (16-bit):** Có $2^{16} = 65,536$ giá trị khả dĩ ($0 - 65535$). Resolver chỉ chấp nhận phản hồi có TXID khớp chính xác với gói truy vấn nó vừa gửi đi.
* **UDP Source Port:** Nếu Resolver dùng cổng cố định (Fixed Port), kẻ tấn công chỉ cần vét cạn (brute-force) 65,536 giá trị TXID. Nếu Resolver áp dụng cơ chế **Source Port Randomization (SPR)**, kẻ tấn công phải đoán đồng thời cả Port ($2^{16}$) và TXID ($2^{16}$), xác suất thành công giảm xuống $1 / (2^{32}) \approx 1 / 4.3 \times 10^9$ (bất khả thi trong thời gian thực).
* **Cache & TTL:** Bản ghi A cụ thể (như `www`) có TTL cao sẽ chặn đứng việc tấn công lặp lại. Kỹ thuật Kaminsky vượt qua cơ chế này bằng cách truy vấn tên miền ngẫu nhiên mới mỗi lần thử.
* **Bản ghi NS (Name Server) & Glue A Record:** Thay vì đầu độc 1 bản ghi A đơn lẻ, payload Kaminsky chèn bản ghi ủy quyền `example.lab10.test. IN NS ns.evil.example.lab10.test.` và bản ghi địa chỉ `ns.evil... IN A 10.10.0.200`. Resolver chấp nhận bản ghi NS này và lưu vào cache, biến Kali thành Authoritative DNS hợp pháp cho toàn bộ zone.

### 1.4. Thực hiện Cache Poisoning an toàn trong môi trường mô phỏng
* Sử dụng miền dành riêng cho kiểm thử: `example.lab10.test` (theo RFC 2606).
* Địa chỉ IP hạ tầng hoàn toàn thuộc dải IP riêng (RFC 1918): `10.9.0.0/24`, `10.10.0.0/24`, `172.16.6.0/24`.
* Lưu lượng tấn công brute-force được relay cục bộ an toàn, không rò rỉ ra ngoài internet.

### 1.5. Kiểm chứng hậu quả và áp dụng giải pháp phòng thủ (Hardening)
* **Hậu quả:** VICTIM gõ `dig` bất kỳ tên miền con nào của `example.lab10.test` hoặc truy cập trình duyệt Web đều bị âm thầm điều hướng sang Web Server giả mạo của Kali (`10.10.0.200`).
* **Phòng thủ & Khôi phục:** Kích hoạt lại BIND9 phiên bản hiện đại, kiểm chứng tính năng **Source Port Randomization (SPR)** qua `tcpdump`, thiết lập **Access Control List (ACL)** triệt tiêu nguy cơ Open Resolver, và kích hoạt DNSSEC.

---

## 2. Mô hình kiến trúc mạng (Network Topology)

Hệ thống gồm 5 máy ảo chạy trên VMware Workstation Pro 17, được liên kết qua tường lửa **pfSense**:

```text
+-----------------------------------------------------------------------------------+
|                                 pfSense 2.7.2                                     |
|  - DNSLAB (opt3 / adapter 5):    10.9.0.1/24                                      |
|  - ATTACKNET (opt4 / adapter 6): 10.10.0.1/24                                     |
|  - DMZ (opt2 / adapter 4):       172.16.6.1/24                                    |
+-------------------+-------------------------------+-------------------------------+
                    |                               |
    +---------------+---------------+               |
    | LAN Segment: dns-lab          |               | LAN Segment: attack-net
    | (10.9.0.0/24)                 |               | (10.10.0.0/24)
    |                               |               |
+---+-------------+   +-------------+---+       +---+-------------------------------+
|  DNS-SERVER     |   |   VICTIM        |       |   ATTACKER (Kali Linux)           |
|  10.9.0.10      |   |   10.9.0.100    |       |   10.10.0.200                     |
|  - BIND9 / Vuln |   |   - Client DNS  |       |   - Remote Poisoning Script       |
|    Resolver     |   |   - Firefox/curl|       |   - Fake DNS Server (UDP 53)      |
+-----------------+   +-----------------+       |   - Fake HTTP Web Server (Port 80)|
                                                +-----------------------------------+
                    |
    +---------------+---------------+
    | LAN Segment: dmz-segment      |
    | (172.16.6.0/24)               |
    |                               |
+---+-------------------------------+---+
|  DMZ-WEB (Ubuntu 24.04)               |
|  - 172.16.6.10: Web Server gốc (Nginx)|
|  - 172.16.6.20: AUTH-DNS Server       |
+---------------------------------------+
```

---

## 3. Bảng phân bổ IP và vai trò các máy ảo

| Máy ảo | Interface | Địa chỉ IP | Vai trò trong bài Lab |
| :--- | :--- | :--- | :--- |
| **pfSense-LAB6** | `opt3` (DNSLAB)<br>`opt4` (ATTACKNET)<br>`opt2` (DMZ) | `10.9.0.1/24`<br>`10.10.0.1/24`<br>`172.16.6.1/24` | Định tuyến L3, Firewall cô lập lưu lượng, ngăn chặn Sniffing giữa các mạng. |
| **DNS-SERVER** | `ens33` | `10.9.0.10/24` | Recursive DNS Resolver trung gian nhận truy vấn từ VICTIM, mục tiêu của đợt tấn công đầu độc Cache. |
| **VICTIM** | `ens33` | `10.9.0.100/24` | Máy nạn nhân truy vấn tên miền, kiểm chứng bị chuyển hướng sang trang web giả mạo. |
| **ATTACKER (Kali)** | `eth0` | `10.10.0.200/24` | Máy tấn công từ xa (Remote Attacker), chạy Fake DNS, Web Server lừa đảo và script bắn gói tin Kaminsky. |
| **DMZ-WEB** | `ens33` | `172.16.6.10/24`<br>`172.16.6.20/24` (Alias) | Máy chủ Web gốc hợp lệ (`172.16.6.10`) và Authoritative DNS Server chính danh của tên miền (`172.16.6.20`). |

---

## 4. Cấu hình Firewall Rules trên pfSense

Trên giao diện pfSense WebGUI (`https://192.168.56.254`), cấu hình các quy tắc tường lửa nghiêm ngặt:

### Quy tắc trên giao diện ATTACKNET (`10.10.0.0/24`)
1. **Pass:** `IPv4 TCP/UDP` | Source: `10.10.0.200` | Destination: `10.9.0.10` | Port: `53` *(Cho phép gửi Query kích hoạt và các gói trả lời DNS giả lập)*.
2. **Pass:** `IPv4 TCP/UDP` | Source: `10.10.0.200` | Destination: `172.16.6.20` | Port: `53, 5300` *(Cho phép giao tiếp với Authoritative DNS & Relay)*.
3. **Block:** `IPv4 *` | Source: `ATTACKNET net` | Destination: `*` *(Chặn toàn bộ truy cập trái phép khác)*.

### Quy tắc trên giao diện DNSLAB (`10.9.0.0/24`)
1. **Pass:** `IPv4 TCP/UDP` | Source: `10.9.0.10` | Destination: `172.16.6.20` | Port: `53` *(Resolver gửi đệ quy sang Authoritative DNS)*.
2. **Pass:** `IPv4 TCP` | Source: `10.9.0.0/24` | Destination: `172.16.6.10` | Port: `80` *(VICTIM truy cập Web Server gốc)*.
3. **Pass:** `IPv4 TCP` | Source: `10.9.0.0/24` | Destination: `10.10.0.200` | Port: `80` *(VICTIM truy cập Web Server giả sau khi bị đầu độc)*.
4. **Block:** `IPv4 *` | Source: `DNSLAB net` | Destination: `*` *(Cô lập an toàn)*.

---

## 5. Tiến trình thực nghiệm chi tiết & Kết quả thực tế

### Bước 1: Baseline DNS hợp lệ & Xác thực cô lập (Remote Verification)
1. **Khởi động AUTH-DNS trên DMZ-WEB (`172.16.6.20`):**
   ```bash
   bash run_auth_dns.sh
   # Lắng nghe tại 172.16.6.20:53 và 172.16.6.20:5300
   ```
2. **Khởi động Resolver trên DNS-SERVER (`10.9.0.10`):**
   ```bash
   python3 vuln_resolver_lab10.py
   # Lắng nghe tại 10.9.0.10:53, chuyển tiếp đệ quy sang 172.16.6.20
   ```
3. **Kiểm tra trạng thái bình thường từ VICTIM (`10.9.0.100`):**
   ```bash
   dig @10.9.0.10 www.example.lab10.test +short
   # Kết quả trả về: 172.16.6.10 (IP Web gốc hợp lệ)
   ```
4. **Xác thực ATTACKER Kali bị cô lập Layer 3 (Remote Sniffing Check):**
   Trên Kali, mở terminal lắng nghe:
   ```bash
   sudo tcpdump -i eth0 -n "udp port 53"
   ```
   Trong khi VICTIM gửi truy vấn liên tục, terminal của Kali ghi nhận **0 packets**. Điều này chứng minh Kali hoàn toàn bị cô lập ở mạng ngoài, không thể bắt lén gói tin nội bộ.

---

### Bước 2: Triển khai tấn công Remote DNS Cache Poisoning (Kaminsky Attack)

Trên máy **ATTACKER (Kali)**, mở 3 Terminal đồng thời:

* **Terminal 1: Khởi động Fake Authoritative DNS Server:**
  ```bash
  sudo python3 evil_dns_lab10.py
  # Output: LAB10 evil authoritative DNS 10.10.0.200:53 for example.lab10.test.
  ```
* **Terminal 2: Khởi động Fake Web Server:**
  ```bash
  sudo python3 -m http.server 80
  # Output: Serving HTTP on 0.0.0.0 port 80 ...
  ```
* **Terminal 3: Bắn payload tấn công Kaminsky:**
  ```bash
  python3 kaminsky_remote_lab10.py
  ```
  * **Cơ chế hoạt động:** Script tự động phát sinh các tên miền con ngẫu nhiên (ví dụ `r8492.example.lab10.test`), gửi query ép `10.9.0.10` phải hỏi ra ngoài. Đồng thời, script bắn một đợt các gói DNS Response giả mạo mang các giá trị Transaction ID được vét cạn kèm bản ghi:
    - **Authority Section:** `example.lab10.test. IN NS ns.evil.example.lab10.test.`
    - **Additional Section:** `ns.evil.example.lab10.test. IN A 10.10.0.200`
  * **Kết quả:** Terminal báo `SUCCESS! Cache poisoned!`.

---

### Bước 3: Kiểm chứng hậu quả trên máy VICTIM (`10.9.0.100`)

1. **Kiểm tra phân giải tên miền con bất kỳ:**
   ```bash
   dig @10.9.0.10 r1.example.lab10.test +short
   dig @10.9.0.10 r2.example.lab10.test +short
   dig @10.9.0.10 r3.example.lab10.test +short
   ```
   **Kết quả thực tế:** Cả 3 lệnh đều trả về **`10.10.0.200`** (IP của Kali)! Bản ghi NS đã chiếm đoạt toàn bộ tên miền.

2. **Cấu hình DNS hệ thống trên VICTIM:**
   ```bash
   echo "nameserver 10.9.0.10" | sudo tee /etc/resolv.conf
   ```

3. **Kiểm tra truy cập Web bằng lệnh `curl`:**
   ```bash
   curl http://www.example.lab10.test
   ```
   **Kết quả:** Trả về mã nguồn HTML của trang Web giả mạo:
   ```html
   <h1>LAB 10 - TRANG WEB GIA MAO (ATTACKER KALI)</h1>
   <p>DNS Cache Poisoning Attack Successful!</p>
   ```

4. **Kiểm tra trên trình duyệt Firefox:**
   Truy cập `http://www.example.lab10.test`, giao diện lập tức hiển thị trang cảnh báo giả mạo màu đỏ do Kali cung cấp thay vì trang Nginx gốc của DMZ-WEB.

---

### Bước 4: Khôi phục BIND9 & Biện pháp phòng thủ Hardening

1. **Dừng Resolver có lỗ hổng và khôi phục BIND9 trên DNS-SERVER:**
   ```bash
   sudo systemctl start bind9
   sudo systemctl status bind9 --no-pager
   # BIND9 active (running)
   ```

2. **Kiểm chứng Source Port Randomization (SPR):**
   * Trên DNS-SERVER, chạy `tcpdump`:
     ```bash
     sudo tcpdump -l -i ens33 -n "udp port 53 and dst host 172.16.6.20"
     ```
   * Trên VICTIM, gửi các truy vấn:
     ```bash
     dig @10.9.0.10 testport1.example.lab10.test
     dig @10.9.0.10 testport2.example.lab10.test
     ```
   * **Kết quả bắt gói tin trên DNS-SERVER:**
     ```text
     03:08:58 IP 10.9.0.10.39956 > 172.16.6.20.53: ...
     03:08:59 IP 10.9.0.10.49752 > 172.16.6.20.53: ...
     03:09:01 IP 10.9.0.10.57904 > 172.16.6.20.53: ...
     03:09:02 IP 10.9.0.10.35960 > 172.16.6.20.53: ...
     ```
     Cổng nguồn UDP biến đổi liên tục (`39956`, `49752`, `57904`, `35960`...). Điều này triệt tiêu hoàn toàn khả năng tấn công Kaminsky vì không thể đoán đồng thời cả Port lẫn TXID.

3. **Kiểm chứng chặn Open Resolver (Access Control List):**
   Từ máy ngoài **KALI (`10.10.0.200`)**, truy vấn phân giải internet:
   ```bash
   dig @10.9.0.10 google.com
   ```
   **Kết quả trả về:** **`status: REFUSED`** *(BIND9 từ chối phục vụ đệ quy cho mạng bên ngoài)*.

---

## 6. Tổng hợp các lỗi thực tế và cách khắc phục

| Hiện tượng lỗi | Nguyên nhân gốc rễ | Cách xử lý triệt để |
| :--- | :--- | :--- |
| `OSError: [Errno 99] Cannot assign requested address` khi chạy `evil_dns_lab10.py` trên Kali. | Kali vừa chuyển sang `attack-net` nên card `eth0` chưa có IP `10.10.0.200/24`. | Gán IP tĩnh `10.10.0.200/24`, Gateway `10.10.0.1` và sửa socket bind về `('0.0.0.0', 53)`. |
| `curl: (6) Could not resolve host: www.exemple...` trên VICTIM. | Sai chính tả tên miền (`exemple` chữ 'e' thay vì `example` chữ 'a') và `/etc/resolv.conf` chưa trỏ `10.9.0.10`. | Gõ đúng `example.lab10.test` và cấu hình `nameserver 10.9.0.10` vào `/etc/resolv.conf`. |
| Lệnh `tcpdump` trên DNS-SERVER không hiện gói tin ngay khi VICTIM truy vấn. | `tcpdump` mặc định gom đầy bộ nhớ đệm (buffer) mới in ra màn hình. | Thêm cờ **`-l`** (`tcpdump -l ...`) để in ngay lập tức theo dòng (Line-buffered). |
| BIND9 ban đầu báo timeout hoặc SERVFAIL khi phân giải ra internet. | Máy lab nội bộ không có kết nối internet ra Root DNS Servers. | Cấu hình forward zone `example.lab10.test` trỏ trực tiếp về `172.16.6.20` trong `named.conf.local`. |

---

## 7. Kết luận

1. **Hiệu quả của tấn công Kaminsky:** Thử nghiệm chứng minh rõ ràng kỹ thuật Kaminsky là bước nhảy vọt so với DNS Spoofing cục bộ. Bằng việc phối hợp giữa truy vấn subdomain ngẫu nhiên (vượt cơ chế TTL Cache) và chèn bản ghi NS giả mạo, kẻ tấn công từ xa có thể chiếm đoạt trọn vẹn toàn bộ không gian tên miền của nạn nhân.
2. **Hiệu quả của các biện pháp phòng thủ:**
   - **Source Port Randomization (SPR):** Nâng độ phức tạp của việc tấn công từ $2^{16}$ lên $2^{32}$, biến việc tấn công vét cạn qua mạng trở nên bất khả thi.
   - **DNSSEC (DNS Security Extensions):** Ký số mật mã lên các bản ghi DNS, giúp Resolver phát hiện và hủy bỏ ngay lập tức các gói tin giả mạo dù đúng cả Port lẫn Transaction ID.
   - **Giới hạn đệ quy (Restricted Recursion):** Ngăn chặn việc máy chủ DNS bị kẻ xấu biến thành bàn đạp tấn công khuếch đại (DNS Amplification DDoS).

---
*Tài liệu được hoàn thiện và kiểm chứng 100% qua thực nghiệm bài lab.*
