# LAB 6 – pfSense, Active Directory, LDAP, Captive Portal và Firewall Policy

## Thông tin sinh viên

- **Họ tên:** Nguyễn Đức Paht
- **MSSV:** 1150080152
- **Lớp:** 11-ĐH-THMT
- **Tên lab:** LAB 6 – pfSense + Active Directory + LDAP + Captive Portal + Firewall Policy

## 1. Môi trường thực hành

- **VMware Workstation Pro 17**
- **pfSense 2.7.2-RELEASE (amd64)**
- **Windows Server 2022** – Domain Controller, AD DS, DNS
- **Windows 11 Client-A** – 10.6.0.21/24
- **Windows 11 Client-B** – 10.6.0.22/24
- **Ubuntu Linux** – DMZ-WEB, dùng lại máy ảo cũ; phiên bản Ubuntu không được xác nhận rõ trong ảnh thực hành
- **Nginx** – máy chủ web mô phỏng các site trong DMZ

### Địa chỉ mạng chính

| Thành phần | IP / Mạng | Vai trò |
|---|---|---|
| pfSense WAN | 192.168.169.139/24 (VMnet8 NAT) | Kết nối Internet |
| pfSense LAN | 10.6.0.1/24 | Gateway cho Client và DC |
| pfSense MGMT | 192.168.56.254/24 | Quản trị WebGUI |
| pfSense DMZ | 172.16.6.1/24 | Gateway DMZ |
| Windows Server / DC01 | 10.6.0.10 | AD DS + DNS + LDAP |
| Client-A | 10.6.0.21 | Máy người dùng A |
| Client-B | 10.6.0.22 | Máy người dùng B |
| GENERAL_SITE | 172.16.6.10 | Web mô phỏng |
| JOB_SITE | 172.16.6.20 | Web mô phỏng |
| SOCIAL_SITE | 172.16.6.30 | Web mô phỏng |
| RESTRICTED_SITE | 172.16.6.40 | Web mô phỏng |

## 2. Cách dựng môi trường

### pfSense

pfSense dùng 4 card mạng:

- WAN → VMnet8 NAT
- MGMT → VMnet1
- LAN → VMnet5
- DMZ → VMnet6

Cấu hình IP cuối:

- WAN: DHCP
- MGMT: 192.168.56.254/24
- LAN: 10.6.0.1/24
- DMZ: 172.16.6.1/24

WebGUI quản trị:

```text
https://192.168.56.254
```

### Windows Server 2022

- Cài Active Directory Domain Services.
- Promote server thành Domain Controller.
- Tạo forest/domain `lab6.test`.
- DC/DNS: `10.6.0.10`.
- Tạo OU `lab6-users`.
- Tạo user `sv_a`, `sv_b`.
- Tạo service account `svc_pfsense_ldap` dùng cho LDAP bind.

### pfSense LDAP

```text
Name: LAB6-AD
Type: LDAP
Host: 10.6.0.10
Port: 389
Transport: Standard TCP
Protocol version: 3
Search scope: Entire Subtree
Base DN: DC=lab6,DC=test
Authentication containers: OU=LAB6-Users,DC=lab6,DC=test
Bind DN: CN=svc_pfsense_ldap,CN=Users,DC=lab6,DC=test
User naming attribute: samAccountName
Group naming attribute: cn
Group member attribute: memberOf
```

Kết quả: `sv_a` và `sv_b` đều xác thực thành công.

### Captive Portal

```text
Zone: LAB6_USERS
Interface: LAN
Authentication Method: Use an Authentication backend
Authentication Server: LAB6-AD
```

Kết quả: Client đăng nhập bằng tài khoản AD và hiện `The portal session is connected.`

### Ubuntu DMZ-WEB

Ubuntu dùng `ens33` với 4 địa chỉ:

```text
172.16.6.10/24
172.16.6.20/24
172.16.6.30/24
172.16.6.40/24
```

Gateway `172.16.6.1`, DNS `8.8.8.8` và `1.1.1.1`.

## 3. Alias

| Alias | Type | Value |
|---|---|---|
| CLIENT_A | Host(s) | 10.6.0.21 |
| CLIENT_B | Host(s) | 10.6.0.22 |
| POLICY_CLIENTS | Host(s) | 10.6.0.21, 10.6.0.22 |
| GENERAL_SITE | Host(s) | 172.16.6.10 |
| JOB_SITE | Host(s) | 172.16.6.20 |
| SOCIAL_SITE | Host(s) | 172.16.6.30 |
| RESTRICTED_SITE | Host(s) | 172.16.6.40 |
| WEB_PORTS | Port(s) | 80, 443 |

## 4. Schedule

Cấu hình cuối:

```text
LUNCH_WINDOW
Mon-Fri
11:30-13:00
```

```text
WORK_HOURS
Mon-Fri
08:00-17:00
```

`TEST_NOW` chỉ dùng để kiểm thử nhanh.

## 5. Các tình huống đã thực hiện

| Tình huống | Kết quả |
|---|---|
| LDAP sv_a / sv_b | **PASS** |
| Captive Portal | **PASS** |
| TH1 – Client-A bị chặn JOB_SITE | **PASS** |
| TH2 – POLICY_CLIENTS bị chặn RESTRICTED_SITE | **PASS** |
| TH3 – Client-B truy cập SOCIAL_SITE theo Schedule | **PASS** |
| TH4 – WEB_PORTS theo WORK_HOURS | **PASS** |
| TH5 – DMZ Isolation | **PASS** |
| TH6–TH7 | **CHƯA THỰC HIỆN** |

## 6. Kết quả chính

- pfSense kết nối TCP/389 tới `10.6.0.10` thành công.
- `sv_a` và `sv_b` xác thực LDAP thành công.
- Captive Portal đăng nhập thành công.
- pfSense WAN ping `8.8.8.8` thành công sau khi đổi sang VMnet8 NAT.
- Ubuntu cài và chạy Nginx thành công.
- TH1: GENERAL_SITE vào được, JOB_SITE bị chặn với Client-A.
- TH2: RESTRICTED_SITE bị chặn và có Firewall Log.
- TH3: SOCIAL_SITE vào được khi schedule active và bị chặn ngoài schedule.
- TH4: HTTP/WEB_PORTS vào được khi schedule active; ngoài schedule bị chặn.
- TH5: Ubuntu `172.16.6.10` ping DC01 `10.6.0.10` bị `100% packet loss`.

## 7. Lỗi gặp phải và cách khắc phục

### WAN pfSense không ra Internet
- **Lỗi:** ping `8.8.8.8` loss.
- **Nguyên nhân:** WAN nối VMnet4 Host-only.
- **Khắc phục:** đổi WAN sang VMnet8 NAT.

### Ubuntu không cài được Nginx
- **Lỗi:** `Temporary failure resolving ...`
- **Nguyên nhân:** DMZ chưa ra Internet / DNS chưa đúng.
- **Khắc phục:** cho DMZ ra Internet tạm thời, dùng NAT, thêm DNS rồi cài lại.

### Netplan sai indentation
- **Lỗi:** `expected mapping (check indentation)`.
- **Khắc phục:** sửa YAML, thêm `nameservers: addresses:` đúng cấp, rồi chạy `netplan generate/apply`.

### LDAP Authentication failed
- **Khắc phục:** kiểm tra TCP/389, Bind DN, reset credential, nhập lại Bind Password và test lại `sv_a`, `sv_b`.

### TH4 không vào được WEB_PORTS
- **Nguyên nhân:** rule Block nằm trên rule Pass.
- **Khắc phục:** đưa `PASS POLICY_CLIENTS → WEB_PORTS [Schedule]` lên trên `BLOCK POLICY_CLIENTS → Any`, Apply và Reset States.

### TH5 vẫn ping được DMZ → LAN
- **Nguyên nhân:** rule Block dùng TCP trong khi ping là ICMP.
- **Khắc phục:** đổi `Protocol = Any`, đặt rule Block DMZ→LAN lên trên rule Allow DMZ Internet.

## 8. File nộp

- Báo cáo Word LAB6.
- `README.md`.
- `LAB6_commands.md`.
- `config.xml` hoặc `LAB6_config.xml`.

Xuất file pfSense tại:

```text
Diagnostics → Backup & Restore
Backup area: All
Download configuration as XML
```
