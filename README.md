# Web安全学习笔记

本仓库包含我学习 DVWA、Burp Suite、Python 自动化脚本等内容的笔记。

## 目录
- [DVWA漏洞复现笔记](./DVWA_Learning_Notes.md)
- [Python脚本](./scripts/)

## 环境
- 靶机：DVWA 1.9
- 攻击机：Kali Linux


## 📚 主要内容

### 1. DVWA 漏洞复现
涵盖：命令注入、文件上传、SQL注入(普通+盲注)、XSS(反射/存储/DOM)、CSRF、文件包含、不安全的验证码、弱会话ID、CSP绕过、JavaScript Attacks、AES-ECB块移动攻击等。每个漏洞记录 Low/Medium/High 难度的手工利用与绕过方法。

### 2. Burp Suite 实战
- Intruder 三种攻击模式（Sniper / Pitchfork / Cluster bomb）
- Grep - Extract 提取响应特征
- Decoder / Comparer / Repeater 模块使用

### 3. Python 自动化脚本
- 目录扫描器：基于字典的目录/文件发现
- SQL 注入检测脚本：携带 Cookie 发送 payload，通过响应长度判断注入点

### 4. 渗透测试实战
- **DC-1**：从 Drupalgeddon2 漏洞获得 shell，利用 SUID find 提权至 root，获取 flag。
- **Linux 提权速查表**：SUID、sudo、Cron、内核漏洞、GTFOBins 查询方法等。

## 🛠️ 使用说明

### 运行 Python 脚本
```bash
# 进入脚本目录，激活虚拟环境（如有）
cd Python_Scripts
python dir_scanner.py http://target.com dict.txt
python sql_inject_check.py http://target.com/sqli/ id 1
