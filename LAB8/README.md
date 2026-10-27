# LAB 8 – Local DNS Attack: BIND9, DNS Spoofing và DNS Cache Poisoning

## Thông tin sinh viên

- **Họ tên:** Nguyễn Đức Phát
- **MSSV:** 1150080152
- **Lớp:** 11-ĐH-THMT
- **Tên lab:** LAB 8 – Local DNS Attack (pfSense + BIND9 + Wireshark + Scapy)
- **Nền tảng:** VMware Workstation Pro 17

> **Về tên:** Tài liệu gốc có các file và domain ghi **LAB 9** (`lab9.test`, `dns_spoof_lab9.py`), nhưng bài đang được lưu/nộp là **LAB 8**. README giữ nguyên tên file/domain của tài liệu để các lệnh chạy khớp với cấu hình.
>
> **An toàn:** Chỉ thực hành DNS spoofing/cache poisoning trên mạng ảo **`dns-lab` `10.9.0.0/24`** do sinh viên quản lý, không gửi gói giả mạo vào mạng thật.

## 1. Môi trường thực hành

- **pfSense:** kế thừa các mạng LAB trước, bổ sung interface DNSLAB riêng.
- **Ubuntu Server 24.04:** DNS-SERVER chạy BIND9 recursive/cache và local zone.
- **Ubuntu Desktop 24.04:** máy VICTIM kiểm tra phân giải DNS/trình duyệt.
- **Kali Linux:** máy ATTACKER dùng Scapy, Wireshark, tcpdump; đồng thời chạy website giả lập.
- **Ubuntu DMZ-WEB:** máy có sẵn từ LAB 7, chạy Nginx và script AUTH-DNS mô phỏng tại IP phụ `172.16.6.20`.

### Địa chỉ mạng chính

| Thành phần        | IP / mạng           | Vai trò                             |
| ----------------- | ------------------- | ----------------------------------- |
| pfSense DNSLAB    | `10.9.0.1/24`       | Gateway / firewall cho mạng DNS-LAB |
| DNS-SERVER        | `10.9.0.10/24`      | Resolver và cache BIND9             |
| VICTIM            | `10.9.0.100/24`     | Client DNS                          |
| Kali ATTACKER     | `10.9.0.200/24`     | Phân tích gói và web giả lập        |
| DMZ-WEB           | `172.16.6.10/24`    | Website Nginx hợp lệ                |
| AUTH-DNS mô phỏng | `172.16.6.20/24`    | IP phụ trên chính DMZ-WEB, UDP 53   |
| pfSense MGMT      | `192.168.56.254/24` | Quản trị pfSense                    |

### Luồng DNS hợp lệ

```text
VICTIM (10.9.0.100)
       |
       | DNS A query (*.lab9.test)
       v
DNS-SERVER (10.9.0.10) – BIND9
       |  lab9.test: zone nội bộ
       |  external.lab9.test: chuyển tiếp theo cấu hình
       v
pfSense DNSLAB (10.9.0.1) -> DMZ
       |
       v
AUTH-DNS (172.16.6.20, trên máy DMZ-WEB)
       |
       +-- www.external.lab9.test -> 172.16.6.10 (kết quả hợp lệ)

Kali (10.9.0.200) -> trang web mô phỏng: http://10.9.0.200
```

## 2. Cách dựng môi trường

### VMware và mạng riêng

- Tạo **LAN Segment** tên `dns-lab` (thay cho VirtualBox Internal Network trong tài liệu).
- Thêm network adapter cho pfSense và tạo interface **DNSLAB** với IP `10.9.0.1/24`, không đặt upstream gateway.
- Kết nối DNS-SERVER, VICTIM và Kali vào **cùng LAN Segment `dns-lab`**.
- Trong giai đoạn cài phần mềm có thể dùng NAT tạm thời; sau đó chuyển về mạng riêng để thực hành.
- Trên các máy Linux, đặt địa chỉ IP tĩnh; gateway là `10.9.0.1` và client dùng DNS `10.9.0.10`.

### Firewall Rules trên pfSense

| Thứ tự | Action      | Source        | Destination       | Protocol / Port |
| ------ | ----------- | ------------- | ----------------- | --------------- |
| 1      | Pass        | `10.9.0.10`   | `172.16.6.20`     | **TCP/UDP 53**  |
| 2      | Pass        | `10.9.0.0/24` | `172.16.6.10`     | TCP 80          |
| 3      | Block + Log | `10.9.0.0/24` | `10.6.0.0/24`     | Any             |
| 4      | Block + Log | `10.9.0.0/24` | `192.168.56.0/24` | Any             |
| 5      | Block + Log | `10.9.0.0/24` | Any               | Any             |

**Sự cố đã sửa:** Rule 1 ban đầu chỉ cho **TCP 53**, làm truy vấn `dig` qua **UDP 53** bị timeout; đổi sang **TCP/UDP** và Apply đã giúp kiểm tra trực tiếp AUTH-DNS thành công.

### DNS-SERVER – Ubuntu Server 24.04 + BIND9

Các tệp cấu hình chính:

```text
/etc/bind/named.conf.options
/etc/bind/named.conf.local
/etc/bind/db.lab9.test
/etc/bind/db.10.9.0
```

Zone nội bộ: `lab9.test`; zone nghịch: `0.9.10.in-addr.arpa`; vùng thử nghiệm chuyển tiếp: `external.lab9.test` đến `172.16.6.20`.

```bash
# Chạy trên DNS-SERVER
ip -br addr
ip route
sudo systemctl is-active bind9
sudo named-checkconf -z
sudo named-checkzone lab9.test /etc/bind/db.lab9.test
sudo named-checkzone 0.9.10.in-addr.arpa /etc/bind/db.10.9.0
dig @10.9.0.10 www.lab9.test A +short
dig @10.9.0.10 -x 10.9.0.10 +short
```

Đã có ảnh `BIND9 active`, zone thuận/nghịch load được và truy vấn `www.lab9.test` trả `172.16.6.10`.

### VICTIM – Ubuntu Desktop 24.04

- IP tĩnh `10.9.0.100/24`, gateway `10.9.0.1`, DNS `10.9.0.10`.
- Lỗi `Cable unplugged` đã từng gặp và xử lý bằng **VMware → Network Adapter → Connected / Connect at power on**.

```bash
# Chạy trên VICTIM
ip -br addr
resolvectl dns
ping -c 4 10.9.0.10
dig @10.9.0.10 www.lab9.test A +short
```

### Kali ATTACKER

- IP tĩnh `10.9.0.200/24`, gateway `10.9.0.1`, DNS `10.9.0.10`.
- Đã cài Scapy, Wireshark, tcpdump và công cụ `dig`.

```bash
# Chạy trên Kali
ip -br addr
ip route
ping -c 4 10.9.0.10
ping -c 4 10.9.0.100
dig @10.9.0.10 www.lab9.test A +short
```

### Website mô phỏng trên Kali

Tạo `~/LAB8/fake_site/index.html` với thông báo **“LAB 8 TRANG MO PHONG CHUYEN HUONG”**, sau đó chạy:

```bash
# Kali: giữ Terminal này chạy khi thử nghiệm
sudo python3 -m http.server 80 --bind 10.9.0.200 --directory "$HOME/LAB8/fake_site"
```

```bash
# Trên Kali hoặc VICTIM
curl http://10.9.0.200
```

**Kết quả đã đạt:** HTTP server `10.9.0.200:80` hoạt động, `curl` và trình duyệt tải được nội dung website mô phỏng.

## 3. AUTH-DNS trên DMZ-WEB

Để tiết kiệm dung lượng, không dựng APP-TEST mới. Dùng lại **DMZ-WEB** đã có sẵn cả `172.16.6.10` và `172.16.6.20` trên card `ens33`.

File thực hành:

```text
auth_dns_delayed.py
```

Chạy trên DMZ-WEB:

```bash
ip -br addr
sudo ss -lunp | grep ':53'
sudo python3 ~/auth_dns_delayed.py --bind 172.16.6.20 --delay 1.5
```

Kiểm tra từ DNS-SERVER:

```bash
dig @172.16.6.20 www.external.lab9.test A +time=5 +tries=1
```

Sau khi sửa Rule 1 TCP/UDP 53, đã có minh chứng **NOERROR, A = `172.16.6.10`** cho truy vấn **trực tiếp** từ DNS-SERVER đến AUTH-DNS.

## 4. Wireshark và baseline DNS

Trên Kali:

```bash
wireshark
```

- Chọn card `eth0` (hoặc card thực tế có IP `10.9.0.200`).
- Display Filter: `dns` hoặc `dns.qry.name == "www.external.lab9.test"`.
- Quan sát Query Name, Transaction ID, UDP source port, IP nguồn/đích, DNS answer.

Trong VMware Workstation, máy Kali **không chắc thấy toàn bộ gói unicast** giữa VICTIM và DNS-SERVER. Nếu không thấy, bắt trực tiếp trên DNS-SERVER:

```bash
sudo tcpdump -i ens33 -nn 'udp port 53 or tcp port 53'
```

**Tình trạng baseline:**

- `www.lab9.test` → `172.16.6.10`: **ĐÃ KIỂM THỬ THÀNH CÔNG**.
- Trực tiếp `@172.16.6.20 www.external.lab9.test`: **ĐÃ KIỂM THỬ THÀNH CÔNG** sau khi sửa firewall.
- Qua BIND9 `@10.9.0.10 www.external.lab9.test`: từng gặp **NXDOMAIN / SERVFAIL / timeout**; lần kiểm tra cuối chưa chứng minh hoạt động ổn định. Cần sửa baseline này trước khi đánh giá Task 2/3.
- Wireshark đã có ảnh bắt DNS tổng quát; **chưa có bằng chứng gói giả mạo của Task 2/3**.

## 5. Ba nhiệm vụ thực hành

| Nhiệm vụ                        | Mục tiêu                                                        | Trạng thái                                        |
| ------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| Task 1 – HOSTS-file redirection | Đổi ánh xạ `www.lab9.test` cục bộ trên VICTIM sang `10.9.0.200` | **PASS – có ảnh Terminal và Firefox thật**        |
| Task 2 – Direct DNS Spoofing    | Quan sát phản hồi DNS giả tác động tới VICTIM                   | **CHƯA XÁC MINH / CHƯA CÓ MINH CHỨNG THÀNH CÔNG** |
| Task 3 – DNS Cache Poisoning    | Quan sát một câu trả lời giả được lưu vào cache resolver        | **CHƯA XÁC MINH / CHƯA CÓ MINH CHỨNG THÀNH CÔNG** |

### Task 1 – HOSTS-file redirection (đã hoàn thành)

Chạy trên **VICTIM**:

```bash
# Sao lưu trước khi thay đổi
sudo cp /etc/hosts /etc/hosts.lab8.bak

# Thêm ánh xạ cục bộ để chuyển www.lab9.test sang Kali
echo '10.9.0.200 www.lab9.test' | sudo tee -a /etc/hosts

# Hỏi bộ phân giải tên miền của hệ điều hành
getent ahostsv4 www.lab9.test

# Truy vấn BIND9 trực tiếp để đối chiếu (không dùng /etc/hosts)
dig @10.9.0.10 www.lab9.test A +short
```

Mở Firefox trên VICTIM tại `http://www.lab9.test` và quan sát trang có dòng **“LAB 8 TRANG MO PHONG CHUYEN HUONG”**, IP `10.9.0.200`.

**Minh chứng thực tế:** đã có ảnh Terminal thêm bản ghi hosts và ảnh Firefox mở đúng trang fake site. Việc này **không phải** bằng chứng DNS cache poisoning, vì `/etc/hosts` được sửa cục bộ trên VICTIM.

Khôi phục sau Task 1:

```bash
sudo cp /etc/hosts.lab8.bak /etc/hosts
sudo resolvectl flush-caches
```

### Task 2 và Task 3 – phần tiếp tục

Tài nguyên gốc có script `dns_spoof_lab9.py` (các chế độ `victim`, `resolver`) và `auth_dns_delayed.py`. Chỉ sử dụng trong mạng LAB đã cô lập. **Chưa ghi các task này thành PASS**; cần baseline `external.lab9.test` đúng, capture query/response và bằng chứng thật trước khi cập nhật README.

## 6. Kết quả chính

- pfSense DNSLAB có 5 rule cô lập và Rule 1 đã sửa sang TCP/UDP 53.
- DNS-SERVER nhận IP `10.9.0.10/24`, BIND9 từng báo `active (running)` và local zone kiểm tra được.
- VICTIM `10.9.0.100` và Kali `10.9.0.200` được nối vào LAN Segment `dns-lab`.
- Kali ping DNS-SERVER và VICTIM **4/4 gói nhận được** trong ảnh thực hành.
- Kali `dig @10.9.0.10 www.lab9.test +short` trả `172.16.6.10`.
- Website giả lập HTTP tại `10.9.0.200:80` truy cập thành công.
- AUTH-DNS mô phỏng trực tiếp tại `172.16.6.20` trả lời `www.external.lab9.test` hợp lệ sau khi sửa rule pfSense.
- **Task 1 PASS:** VICTIM đổi `/etc/hosts`, Firefox truy cập `www.lab9.test` hiển thị trang Kali.
- Vẫn còn lỗi forwarding/authoritative cho `external.lab9.test` trong các lần kiểm tra cuối.

## 7. Lỗi gặp phải và cách khắc phục

### VICTIM báo `Cable unplugged`

- **Nguyên nhân:** card mạng ảo chưa Connected.
- **Khắc phục:** bật `Connected` và `Connect at power on` trên VMware, cùng LAN Segment `dns-lab`.

### BIND9 báo `file not found` với zone nghịch

- **Nguyên nhân:** sai đường dẫn hoặc thiếu file `db.10.9.0`.
- **Khắc phục:** tạo file tại `/etc/bind/db.10.9.0`, kiểm tra `named-checkzone`.

### `forward` unexpected trong `named.conf.local`

- **Nguyên nhân:** lỗi nhập cú pháp `forward`.
- **Khắc phục:** sửa từ khóa rồi chạy `named-checkconf`.

### `bad dotted quad` khi kiểm tra zone

- **Nguyên nhân:** bản ghi `A` bị điền hostname thay vì IPv4.
- **Khắc phục:** dùng giá trị IPv4 như `172.16.6.20`.

### Cảnh báo NS bị nối tên hai lần

- **Hiện tượng:** `ns.external.lab9.test.lab9.test`.
- **Nguyên nhân thường gặp:** thiếu dấu chấm cuối FQDN; cần kiểm tra bản ghi NS/glue và delegation.

### `dig @172.16.6.20` timeout

- **Nguyên nhân đã tìm thấy:** pfSense Rule 1 chỉ cho TCP 53, còn `dig` mặc định hỏi UDP 53.
- **Khắc phục:** đổi giao thức thành TCP/UDP, lưu và Apply; sau đó truy vấn trực tiếp đã trả `NOERROR`.

### `www.external.lab9.test` trả NXDOMAIN / SERVFAIL / timeout qua BIND9

- **Tình trạng:** chưa xác minh dứt điểm trong lần cuối; có thể liên quan quan hệ zone cha `lab9.test` / zone con `external.lab9.test`, forwarder hoặc quá trình phục vụ DNS.
- **Cách kiểm tra tiếp:**

```bash
sudo systemctl status bind9 --no-pager -l
sudo named-checkconf -z
sudo ss -lunpt | grep ':53'
dig @172.16.6.20 www.external.lab9.test A +time=5 +tries=1
dig @10.9.0.10 www.external.lab9.test A +time=5 +tries=1
sudo journalctl -u named -n 30 --no-pager
```

Không đánh dấu forwarding PASS chỉ dựa vào `named-checkzone OK`.

## 8. File nộp và minh chứng

Nên lưu các ảnh thật vào `images/` và đặt tên rõ ràng, chẳng hạn:

1. DNSLAB interface / 5 firewall rules và Rule 1 TCP/UDP.
2. BIND9 active, kiểm tra zone thuận/nghịch.
3. VICTIM IP/DNS và Kali IP, ping.
4. Website giả lập trên Kali.
5. AUTH-DNS trên DMZ-WEB và kết quả `NOERROR` trực tiếp.
6. Wireshark / tcpdump lưu lượng DNS.
7. **Task 1:** Terminal `/etc/hosts` và Firefox vào fake site.
8. Task 2/3 và restore: bổ sung **chỉ khi có ảnh thực nghiệm thật**.

Cấu trúc GitHub đề xuất:

```text
LAB8/
├── README.md
├── images/                     # Ảnh màn hình thực tế
├── scripts/                    # Script bài lab nếu được phép chia sẻ
└── reports/                    # Tài liệu báo cáo
```

**Không đăng mật khẩu, private key, token hay ảnh chứa thông tin truy cập thật lên GitHub.**

## 9. Kết luận

LAB 8 đã dựng được môi trường DNS-LAB trên VMware với pfSense, BIND9, VICTIM, Kali và AUTH-DNS dùng chung DMZ-WEB. Đã kiểm thử DNS nội bộ, kết nối máy ảo, web mô phỏng và **hoàn thành Task 1 – HOSTS-file redirection**. Phần forwarding `external.lab9.test` qua BIND9 cần hoàn thiện cho ổn định; Task 2 và Task 3 chưa có minh chứng kết quả thành công nên được ghi đúng là chưa xác minh.
