帮我全面重构这个代码仓：
1. 全面按照以下idea优化改造工具，不要考虑兼容性，直接移除不需要的工具，考虑在描述中加入工具的基本描述，什么时候使用这个工具，什么时候不应该使用，使用的示例。
工具名称,参数 (Parameters),LLM 侧描述 (Description)
list_servers,无,【用途】 获取本地保存的所有远程服务器配置清单。包含 ID、主机名、用户名及其在线状态。【何时使用】 当用户提到“连接服务器”、“查看机器”或未指定目标 ID 时，首先调用此工具查看可用资源。【示例】 “查看我有哪些服务器。”
save_server,"connection_id, host, user, auth_type, credential, port",【用途】 持久化保存服务器连接信息到本地加密库。支持自定义 SSH 端口、password 或 private_key。【何时使用】 当用户提供新的服务器信息，或由于现有凭据失效（AUTH_FAILED）需要更新时调用。【注意事项】 成功保存后，后续操作仅需引用 connection_id。请勿在对话中重复索要已保存的信息。【示例】 “保存我的服务器，IP x.x.x.x，用户 root，端口 2222，密码 xxx。”
remove_server,connection_id,【用途】 从本地库中彻底删除指定的服务器配置。【何时使用】 仅当用户明确要求“忘记”、“删除”或“移除”某台机器的配置时使用。【注意事项】 操作不可逆，删除后需重新调用 save_server 才能再次连接。
execute_command,"connection_id, command","【用途】 在远程服务器上执行非交互式 Shell 命令并返回结果。【何时使用】 所有的状态查询（ls, top, df）、文件操作（cp, mv）或脚本运行。【不适用场景】 严禁执行需要实时交互的命令（如 vim, htop, 或需要手动确认 [Y/n] 的命令，除非使用了 -y 参数）。【注意事项】 如涉及敏感目录，请尝试使用 sudo 前缀。【示例】 execute_command(connection_id=""srv1"", command=""df -h"")"
upload_file,"connection_id, local_path, remote_path","【用途】 将本地计算机的文件安全传输到远程服务器。【何时使用】 部署配置文件、上传脚本或代码包到远程。【注意事项】 确保远程目标目录存在写权限。如果 remote_path 仅是一个目录，文件名将保持与本地一致。【示例】 upload_file(connection_id=""srv1"", local_path=""./config.yaml"", remote_path=""/etc/app/"")"
download_file,"connection_id, remote_path, local_path","【用途】 从远程服务器抓取文件到本地计算机。【何时使用】 查看远程日志文件、获取备份数据或检查远程生成的报告。【注意事项】 下载大文件（>100MB）前应先通过 execute_command 检查其大小，以免造成传输超时或内存溢出。【示例】 download_file(connection_id=""srv1"", remote_path=""/var/log/syslog"", local_path=""./logs/"")"
2. 同时注意在mcp sever返回结果中加入具体信息，使得LLM能够进行其他尝试，比如Error: Connection failed. Incorrect password (auth_failed)， 这个时候LLM能够让用户更新密码。
3. 在 upload_file 和 download_file 的逻辑里，如果 LLM 没给 local_path，工具应该能够自动设置，并在返回结果中将路径返回给llm
4. 连接状态缓存
在 list_servers 的返回结果中，加入一个 last_connected 时间戳。 效果： LLM 会倾向于使用最近刚刚成功连接过的服务器，这能提高任务的成功率。
5. 持久化保存放在~/.config/remoteshell/hosts.json中，llm负责调用工具更新创建连接，用户只需要于LLM交互即可，对于用户侧来说，需要在 mcpServers 里写一行 "command": "uvx", "args": ["remoteshell-mcp"]即可，并在readme中说明~/.config/remoteshell/hosts.json这个路径LLM会将连接持久化保存到这里，也可以手动修改这个文件，并给出示例
6. 简化readme，仅提供一种配置方式即"command": "uvx", "args": ["remoteshell-mcp"]这种配置方式的示例，当前Claude code的快捷配置保留。
7.我和你的对话可以用英文，但是写代码注释，readme之类的必须用英文。
8.通过fastmcp修饰工具的时候，使用fastmcp这个mcp工具来搜索如何使用fastmcp这个python包，他已经更新到2.0.0以上了，尤其是涉及mcp tool的工具描述和参数的时候