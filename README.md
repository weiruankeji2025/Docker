# Docker 迁移工具

**作者：威软科技**

一款简单、可靠、易用的 Docker 容器和镜像迁移工具，帮助您轻松完成 Docker 环境的备份、迁移和恢复。

## ✨ 特性

- 🚀 **操作简单** - 一行命令完成备份和恢复
- 🛡️ **可靠安全** - 完整的错误处理和日志记录
- 📦 **功能完整** - 支持镜像、容器、数据卷的导出导入
- 🎨 **界面友好** - 彩色命令行输出，进度清晰可见
- 📝 **自动报告** - 自动生成迁移清单和日志文件
- 🔍 **资源查看** - 快速查看当前 Docker 资源

## 📋 系统要求

- Python 3.6+
- Docker Engine 已安装并运行
- 足够的磁盘空间用于存储备份文件

## 🔧 安装

1. 克隆或下载本项目：

```bash
git clone <repository-url>
cd Docker
```

2. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

3. 确保 Docker 正在运行：

```bash
docker ps
```

## 📖 使用方法

### 查看所有 Docker 资源

```bash
python docker_migrate.py list
```

显示当前系统中的所有镜像、容器、数据卷和网络。

### 导出镜像

导出所有镜像：

```bash
python docker_migrate.py export-images
```

导出特定镜像：

```bash
python docker_migrate.py export-images --images nginx:latest redis:latest mysql:8.0
```

导出到指定目录：

```bash
python docker_migrate.py export-images --output-dir /path/to/backup
```

### 导入镜像

从默认备份目录导入：

```bash
python docker_migrate.py import-images
```

从指定目录导入：

```bash
python docker_migrate.py import-images --dir /path/to/images
```

### 导出容器配置

导出所有容器的配置：

```bash
python docker_migrate.py export-containers
```

导出特定容器：

```bash
python docker_migrate.py export-containers --containers web-app database
```

### 完整备份

一键备份所有 Docker 资源：

```bash
python docker_migrate.py backup
```

指定备份名称：

```bash
python docker_migrate.py backup --name my-backup-20260101
```

备份将保存到 `./docker_backup/` 目录下，包含：
- 所有镜像的 tar 文件
- 所有容器的配置 JSON 文件
- 所有数据卷的信息文件
- 备份清单 manifest.json

### 从备份恢复

```bash
python docker_migrate.py restore --backup ./docker_backup/docker_backup_20260101_120000
```

## 📁 备份目录结构

```
docker_backup/
├── docker_backup_20260101_120000/
│   ├── manifest.json              # 备份清单
│   ├── images/                    # 镜像文件
│   │   ├── nginx_latest.tar
│   │   └── redis_latest.tar
│   ├── containers/                # 容器配置
│   │   ├── web-app_config.json
│   │   └── database_config.json
│   └── volumes/                   # 数据卷信息
│       └── data-vol_info.json
└── migration_20260101_120000.log  # 操作日志
```

## 🔍 备份清单示例

```json
{
  "backup_name": "docker_backup_20260101_120000",
  "backup_time": "2026-01-01T12:00:00",
  "backup_by": "威软科技 Docker迁移工具",
  "images": {
    "nginx:latest": {
      "file": "images/nginx_latest.tar",
      "size": 142.5,
      "id": "abc123def456"
    }
  },
  "containers": {
    "web-app": {
      "name": "web-app",
      "image": "nginx:latest",
      "status": "running"
    }
  },
  "statistics": {
    "total_images": 3,
    "total_containers": 5,
    "total_volumes": 2
  }
}
```

## 💡 使用场景

1. **服务器迁移** - 将 Docker 环境从一台服务器迁移到另一台
2. **环境备份** - 定期备份生产环境的 Docker 配置
3. **开发环境同步** - 在团队成员间同步开发环境
4. **灾难恢复** - 快速恢复损坏的 Docker 环境
5. **版本管理** - 保存不同版本的 Docker 环境快照

## ⚙️ 高级选项

### 自定义输出目录

```bash
python docker_migrate.py backup --output-dir /mnt/backup/docker
```

### 选择性导出

只导出特定的资源而不是全部：

```bash
# 只导出 Web 相关镜像
python docker_migrate.py export-images --images nginx:latest php:8.0 mysql:8.0

# 只导出运行中的容器
python docker_migrate.py export-containers --containers app1 app2
```

## 📝 日志文件

每次操作都会生成详细的日志文件，包含：
- 操作时间戳
- 成功/失败的操作记录
- 错误详情和堆栈信息

日志文件位置：`./docker_backup/migration_YYYYMMDD_HHMMSS.log`

## ⚠️ 注意事项

1. **磁盘空间** - 确保有足够的磁盘空间存储导出的镜像文件
2. **权限问题** - 需要有 Docker 操作权限（通常需要 sudo 或加入 docker 组）
3. **容器状态** - 导出的是容器配置，不是容器的实时数据
4. **数据卷** - 数据卷的实际数据需要单独备份
5. **网络配置** - 自定义网络配置需要手动重建

## 🔒 安全建议

- 定期备份重要的 Docker 环境
- 将备份文件存储在安全的位置
- 敏感数据（如密码、密钥）应使用 Docker secrets 或环境变量管理
- 传输备份文件时使用加密通道

## 🐛 故障排除

### 无法连接到 Docker

```bash
# 检查 Docker 服务状态
sudo systemctl status docker

# 启动 Docker 服务
sudo systemctl start docker
```

### 权限被拒绝

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

### 导入失败

- 检查镜像文件是否完整
- 确保 Docker 版本兼容
- 查看日志文件了解详细错误信息

## 📞 支持与反馈

遇到问题或有建议？欢迎联系：

- 开发者：威软科技
- 项目主页：[GitHub Repository]

## 📄 许可证

本项目遵循 LICENSE 文件中的许可证条款。

## 🙏 致谢

感谢使用威软科技的 Docker 迁移工具！

---

**威软科技** - 让 Docker 迁移更简单