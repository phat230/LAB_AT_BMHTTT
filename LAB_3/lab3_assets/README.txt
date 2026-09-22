LAB3 THREATS ASSETS - 14/09/2026

Tat ca tep trong goi nay chi dung cho bai thuc hanh an toan trong VM thuoc quyen quan ly.
- www/index.html: trang HTTP cuc bo de quan sat plaintext tren loopback.
- sysmon-lab.xml: cau hinh Sysmon toi thieu theo schema 4.90, ghi ProcessCreate, NetworkConnect, FileCreate, RegistryEvent.
- scripts/local_load_test.py: tao 50 request, 5 worker, hard-code 127.0.0.1:8080; khong nhan URL tu nguoi dung.
- samples/phishing_email.txt: mau phishing OFFLINE, su dung domain .example/.invalid.
- samples/social_engineering_cases.csv: tinh huong de phan loai Social Engineering.
- data/ddos_sample.csv: dataset huan luyen offline su dung cac day dia chi TEST-NET RFC 5737.
- data/mailbomb_sample.csv: dataset log email huan luyen offline; khong gui email.

Khong sua script local_load_test.py de nham vao dia chi khac 127.0.0.1.
