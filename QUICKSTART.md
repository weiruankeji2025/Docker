# 快速入门指南

**威软科技 Docker 迁移工具**

## 5 分钟快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 查看帮助信息

```bash
python docker_migrate.py -h
```

### 3. 查看当前 Docker 资源

```bash
python docker_migrate.py list
```

### 4. 一键完整备份

```bash
python docker_migrate.py backup
```

备份文件将保存在 `./docker_backup/` 目录下。

### 5. 从备份恢复

```bash
python docker_migrate.py restore --backup ./docker_backup/docker_backup_YYYYMMDD_HHMMSS
```

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 查看资源 | `python docker_migrate.py list` |
| 导出所有镜像 | `python docker_migrate.py export-images` |
| 导出特定镜像 | `python docker_migrate.py export-images --images nginx:latest` |
| 导入镜像 | `python docker_migrate.py import-images` |
| 导出容器配置 | `python docker_migrate.py export-containers` |
| 完整备份 | `python docker_migrate.py backup` |
| 从备份恢复 | `python docker_migrate.py restore --backup <path>` |

## 典型使用场景

### 场景 1：服务器迁移

在**源服务器**上：

```bash
# 1. 完整备份
python docker_migrate.py backup --name server-migration-2026

# 2. 打包备份文件
tar -czf docker-backup.tar.gz docker_backup/server-migration-2026
```

在**目标服务器**上：

```bash
# 1. 解压备份文件
tar -xzf docker-backup.tar.gz

# 2. 恢复备份
python docker_migrate.py restore --backup docker_backup/server-migration-2026
```

### 场景 2：定期备份

创建备份脚本 `auto_backup.sh`：

```bash
#!/bin/bash
cd /path/to/Docker
python docker_migrate.py backup --name "auto-backup-$(date +%Y%m%d)"
```

添加到 crontab 每天凌晨 2 点执行：

```bash
0 2 * * * /path/to/auto_backup.sh
```

### 场景 3：选择性迁移

只迁移特定的镜像和容器：

```bash
# 导出特定镜像
python docker_migrate.py export-images --images nginx:latest mysql:8.0

# 导出特定容器配置
python docker_migrate.py export-containers --containers web-app database
```

## 注意事项

1. 确保有足够的磁盘空间
2. 运行工具时需要 Docker 权限
3. 容器数据卷需要单独备份
4. 查看日志文件了解详细信息

## 获取帮助

遇到问题？查看完整文档：

```bash
cat README.md
```

或联系：**威软科技**

---

开始使用吧！一行命令，轻松迁移 Docker 环境。
