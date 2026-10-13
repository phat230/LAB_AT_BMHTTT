# LAB6 – Tổng hợp lệnh đã sử dụng

**Sinh viên:** Nguyễn Đức Paht  
**MSSV:** 1150080152  
**Lớp:** 11-ĐH-THMT

## Windows Server 2022 / PowerShell

```powershell
Resolve-DnsName lab6.test
```

```powershell
Get-ADUser sv_a -Properties DistinguishedName,Enabled
```

```powershell
Get-ADUser svc_pfsense_ldap -Properties DistinguishedName,Enabled
```

```powershell
Set-ADAccountPassword svc_pfsense_ldap -Reset `
-NewPassword (Read-Host -AsSecureString "New password")

Unlock-ADAccount svc_pfsense_ldap
Enable-ADAccount svc_pfsense_ldap
```

```powershell
Add-Type -AssemblyName System.DirectoryServices.AccountManagement

$cred = Get-Credential "LAB6\svc_pfsense_ldap"

$ctx = New-Object System.DirectoryServices.AccountManagement.PrincipalContext(
    'Domain',
    'lab6.test'
)

$ctx.ValidateCredentials(
    'svc_pfsense_ldap',
    $cred.GetNetworkCredential().Password
)
```

```powershell
Get-ADUser sv_a -Properties Enabled,LockedOut,DistinguishedName |
Select Enabled,LockedOut,DistinguishedName
```

```powershell
Set-ADAccountPassword sv_b -Reset `
-NewPassword (Read-Host -AsSecureString "New password for sv_b")

Unlock-ADAccount sv_b
Enable-ADAccount sv_b
Set-ADUser sv_b -ChangePasswordAtLogon $false
```

```powershell
Get-ADUser sv_b -Properties Enabled,LockedOut,PasswordExpired,PasswordLastSet |
Select SamAccountName,Enabled,LockedOut,PasswordExpired,PasswordLastSet
```

```powershell
Add-Type -AssemblyName System.DirectoryServices.AccountManagement

$cred = Get-Credential "LAB6\sv_b"

$ctx = New-Object System.DirectoryServices.AccountManagement.PrincipalContext(
    'Domain',
    'lab6.test'
)

$ctx.ValidateCredentials(
    'sv_b',
    $cred.GetNetworkCredential().Password
)
```

## Ubuntu DMZ-WEB

```bash
ip -br addr
ls /etc/netplan
sudo cat /etc/netplan/00-installer-config.yaml
```

```bash
sudo cp /etc/netplan/00-installer-config.yaml /etc/netplan/00-installer-config.yaml.bak
sudo nano /etc/netplan/00-installer-config.yaml
```

Netplan cuối:

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: false
      addresses:
        - 172.16.6.10/24
        - 172.16.6.20/24
        - 172.16.6.30/24
        - 172.16.6.40/24
      routes:
        - to: default
          via: 172.16.6.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

```bash
sudo netplan generate
sudo netplan apply
ip -br addr
ip route
resolvectl status
```

```bash
ping -c 4 172.16.6.1
ping -c 4 8.8.8.8
ping -c 4 google.com
```

```bash
sudo apt update
sudo apt install nginx -y
sudo systemctl enable --now nginx
systemctl status nginx
```

```bash
curl http://172.16.6.10
curl http://172.16.6.20
curl http://172.16.6.30
curl http://172.16.6.40
```

TH5:

```bash
ping -c 4 10.6.0.10
```

Kết quả cuối:

```text
4 packets transmitted, 0 received, 100% packet loss
```

## Windows 11 Client-A / Client-B

```cmd
ipconfig
ping 10.6.0.1
```

Test web:

```text
http://172.16.6.10
http://172.16.6.20
http://172.16.6.30
http://172.16.6.40
```

Có thể test:

```cmd
curl.exe -I http://172.16.6.30
```

## pfSense LDAP

```text
LAB6-AD
Host: 10.6.0.10
Port: 389
Base DN: DC=lab6,DC=test
Authentication Containers: OU=LAB6-Users,DC=lab6,DC=test
Bind DN: CN=svc_pfsense_ldap,CN=Users,DC=lab6,DC=test
User naming attribute: samAccountName
Group naming attribute: cn
Group member attribute: memberOf
```

## Captive Portal

```text
Zone: LAB6_USERS
Interface: LAN
Authentication: LAB6-AD
```

## Alias

```text
CLIENT_A        = 10.6.0.21
CLIENT_B        = 10.6.0.22
POLICY_CLIENTS  = 10.6.0.21, 10.6.0.22
GENERAL_SITE    = 172.16.6.10
JOB_SITE        = 172.16.6.20
SOCIAL_SITE     = 172.16.6.30
RESTRICTED_SITE = 172.16.6.40
WEB_PORTS       = 80,443   (Type: Port(s))
```

## Rule logic

TH1:

```text
BLOCK CLIENT_A → JOB_SITE TCP/80
PASS  CLIENT_A → GENERAL_SITE TCP/80
```

TH2:

```text
BLOCK POLICY_CLIENTS → RESTRICTED_SITE TCP/80
PASS  POLICY_CLIENTS → GENERAL_SITE TCP/80
```

TH3:

```text
PASS  CLIENT_B → SOCIAL_SITE TCP/80 [LUNCH_WINDOW]
BLOCK CLIENT_B → SOCIAL_SITE TCP/80
```

TH4:

```text
PASS  POLICY_CLIENTS → Any → WEB_PORTS [WORK_HOURS]
BLOCK POLICY_CLIENTS → Any
```

TH5:

```text
BLOCK DMZ subnets → LAN subnets
Protocol: Any
```

## Reset States

```text
Diagnostics → States → Reset States
```

## Xuất config.xml

```text
Diagnostics → Backup & Restore
Backup area: All
Download configuration as XML
```
