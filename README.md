Web安全学习笔记
从漏洞原理到渗透实战，记录我的安全学习之路。

内容概览
DVWA：SQL注入、XSS、CSRF、文件上传、文件包含、命令注入、CSP绕过、JavaScript Attacks、AES-ECB块移动攻击（含Low/Medium/High难度绕过）

Burp Suite：Proxy、Repeater、Intruder（Sniper/Pitchfork/Cluster bomb）、Decoder、Comparer、Grep-Extract

Python脚本：目录扫描器、SQL注入检测脚本（requests库，携带Cookie）

DC系列靶机：DC-1（Drupalgeddon2 -> SUID提权）、DC-2（WordPress爆破 -> rbash绕过 -> sudo git提权）、DC-3（Joomla SQL注入 -> 内核提权）

Linux提权：SUID/SGID、环境变量劫持（LD_PRELOAD/LD_LIBRARY_PATH）、Cron劫持（PATH/通配符）、MySQL UDF、NFS、内核漏洞等10+种手法，已完成TryHackMe Linux PrivEsc全房间

仓库结构

├── img/                      # 截图存放
├── notes/                    # 所有学习笔记
│   ├── 测试.md               # DVWA漏洞复现笔记
│   ├── DC1/2/3.md            # DC-1/2/3渗透报告
│   └── Linux-PrivEsc/        # 提权速查表及详细笔记
├── script/                   # Python脚本
│   ├── dir_scanner.py        # 目录扫描器
│   └── sql_inject_check.py   # SQL注入检测脚本
└── README.md
技能一览
Web安全：OWASP Top 10核心漏洞原理与利用

渗透工具：Nmap、SQLMap、WPScan、JoomScan、Burp Suite、Metasploit

操作系统：Kali Linux、Linux提权（10+种手法）

开发语言：Python（自动化脚本）、Shell、SQL

报告输出：渗透测试报告撰写（含漏洞描述 + 复现步骤 + 修复建议）

快速开始
text
git clone https://github.com/hsg1224/Web-Security-Learning.git
cd Web-Security-Learning/script

# 目录扫描器
python dir_scanner.py http://target.com dict.txt -t 20

# SQL注入检测
python sql_inject_check.py http://target.com/sqli/ id 1 -c "cookie_str"
依赖安装：pip install requests bs4

学习进度
[+] DVWA全模块（Low/Medium/High）

[+] DC-1 / DC-2 / DC-3完整渗透

[+] TryHackMe Linux PrivEsc全房间

[-]内网横向移动 / SRC漏洞挖掘（计划中）
联系我
GitHub：hsg1224

邮箱：2749884910@qq.com

求职意向：安全服务工程师 / 渗透测试实习生（杭州 / 广州）

本仓库所有内容仅供学习交流使用，请勿用于非法用途。
