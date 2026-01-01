#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker迁移工具
作者：威软科技
功能：简单、可靠、易用的Docker容器和镜像迁移工具
"""

import os
import sys
import json
import tarfile
import argparse
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

try:
    import docker
    from docker.errors import DockerException
except ImportError:
    print("错误：请先安装 docker 库")
    print("运行：pip install docker")
    sys.exit(1)


class Colors:
    """命令行颜色输出"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


class DockerMigrationTool:
    """Docker迁移工具主类"""

    def __init__(self, output_dir: str = "./docker_backup"):
        """
        初始化Docker迁移工具

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置日志
        self.setup_logging()

        # 连接Docker
        try:
            self.client = docker.from_env()
            self.client.ping()
            self.logger.info("成功连接到Docker守护进程")
        except DockerException as e:
            self.logger.error(f"无法连接到Docker: {e}")
            print(f"{Colors.FAIL}错误：无法连接到Docker守护进程{Colors.END}")
            print(f"请确保Docker已安装并正在运行")
            sys.exit(1)

    def setup_logging(self):
        """设置日志系统"""
        log_file = self.output_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def print_header(self, text: str):
        """打印标题"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

    def print_success(self, text: str):
        """打印成功信息"""
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")

    def print_error(self, text: str):
        """打印错误信息"""
        print(f"{Colors.FAIL}✗ {text}{Colors.END}")

    def print_info(self, text: str):
        """打印信息"""
        print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

    def list_resources(self):
        """列出所有Docker资源"""
        self.print_header("Docker 资源列表")

        # 列出镜像
        print(f"{Colors.BOLD}镜像列表：{Colors.END}")
        images = self.client.images.list()
        if images:
            for idx, img in enumerate(images, 1):
                tags = img.tags if img.tags else ["<无标签>"]
                size_mb = img.attrs['Size'] / (1024 * 1024)
                print(f"  {idx}. {tags[0]} ({size_mb:.2f} MB)")
        else:
            print(f"  {Colors.WARNING}无镜像{Colors.END}")

        # 列出容器
        print(f"\n{Colors.BOLD}容器列表：{Colors.END}")
        containers = self.client.containers.list(all=True)
        if containers:
            for idx, container in enumerate(containers, 1):
                status = container.status
                color = Colors.GREEN if status == 'running' else Colors.WARNING
                print(f"  {idx}. {container.name} [{color}{status}{Colors.END}]")
        else:
            print(f"  {Colors.WARNING}无容器{Colors.END}")

        # 列出卷
        print(f"\n{Colors.BOLD}数据卷列表：{Colors.END}")
        volumes = self.client.volumes.list()
        if volumes:
            for idx, volume in enumerate(volumes, 1):
                print(f"  {idx}. {volume.name}")
        else:
            print(f"  {Colors.WARNING}无数据卷{Colors.END}")

        # 列出网络
        print(f"\n{Colors.BOLD}网络列表：{Colors.END}")
        networks = self.client.networks.list()
        if networks:
            for idx, network in enumerate(networks, 1):
                if network.name not in ['bridge', 'host', 'none']:
                    print(f"  {idx}. {network.name}")
        else:
            print(f"  {Colors.WARNING}无自定义网络{Colors.END}")

    def export_images(self, image_names: Optional[List[str]] = None) -> Dict:
        """
        导出镜像

        Args:
            image_names: 要导出的镜像名称列表，为None时导出所有镜像

        Returns:
            导出信息字典
        """
        self.print_header("导出镜像")

        images = self.client.images.list()
        if not images:
            self.print_info("没有镜像需要导出")
            return {}

        export_info = {}
        images_dir = self.output_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # 筛选要导出的镜像
        if image_names:
            images = [img for img in images if any(tag in image_names for tag in img.tags)]

        for img in images:
            try:
                tags = img.tags if img.tags else [f"image_{img.short_id}"]
                tag = tags[0]

                # 创建安全的文件名
                safe_name = tag.replace(':', '_').replace('/', '_')
                output_file = images_dir / f"{safe_name}.tar"

                self.print_info(f"正在导出镜像: {tag}")

                # 导出镜像
                with open(output_file, 'wb') as f:
                    for chunk in img.save(named=True):
                        f.write(chunk)

                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                self.print_success(f"已导出: {tag} ({file_size_mb:.2f} MB)")

                export_info[tag] = {
                    'file': str(output_file),
                    'size': file_size_mb,
                    'id': img.short_id
                }

            except Exception as e:
                self.logger.error(f"导出镜像 {tag} 失败: {e}")
                self.print_error(f"导出失败: {tag}")

        return export_info

    def import_images(self, images_dir: Optional[str] = None):
        """
        导入镜像

        Args:
            images_dir: 镜像文件目录
        """
        self.print_header("导入镜像")

        if images_dir is None:
            images_dir = self.output_dir / "images"
        else:
            images_dir = Path(images_dir)

        if not images_dir.exists():
            self.print_error(f"目录不存在: {images_dir}")
            return

        tar_files = list(images_dir.glob("*.tar"))
        if not tar_files:
            self.print_info("没有找到镜像文件")
            return

        for tar_file in tar_files:
            try:
                self.print_info(f"正在导入: {tar_file.name}")

                with open(tar_file, 'rb') as f:
                    images = self.client.images.load(f.read())

                for img in images:
                    tags = img.tags if img.tags else [img.short_id]
                    self.print_success(f"已导入镜像: {tags[0]}")

            except Exception as e:
                self.logger.error(f"导入镜像 {tar_file.name} 失败: {e}")
                self.print_error(f"导入失败: {tar_file.name}")

    def export_containers(self, container_names: Optional[List[str]] = None) -> Dict:
        """
        导出容器配置

        Args:
            container_names: 要导出的容器名称列表，为None时导出所有容器

        Returns:
            导出信息字典
        """
        self.print_header("导出容器配置")

        containers = self.client.containers.list(all=True)
        if not containers:
            self.print_info("没有容器需要导出")
            return {}

        # 筛选要导出的容器
        if container_names:
            containers = [c for c in containers if c.name in container_names]

        export_info = {}
        containers_dir = self.output_dir / "containers"
        containers_dir.mkdir(exist_ok=True)

        for container in containers:
            try:
                self.print_info(f"正在导出容器配置: {container.name}")

                # 保存容器配置
                config = {
                    'name': container.name,
                    'image': container.image.tags[0] if container.image.tags else container.image.short_id,
                    'status': container.status,
                    'ports': container.ports,
                    'environment': container.attrs['Config']['Env'],
                    'volumes': container.attrs['Mounts'],
                    'network_settings': container.attrs['NetworkSettings'],
                    'command': container.attrs['Config']['Cmd'],
                    'entrypoint': container.attrs['Config']['Entrypoint'],
                    'working_dir': container.attrs['Config']['WorkingDir'],
                    'labels': container.attrs['Config']['Labels']
                }

                config_file = containers_dir / f"{container.name}_config.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                self.print_success(f"已导出配置: {container.name}")
                export_info[container.name] = config

            except Exception as e:
                self.logger.error(f"导出容器 {container.name} 配置失败: {e}")
                self.print_error(f"导出失败: {container.name}")

        return export_info

    def export_volumes(self) -> Dict:
        """导出数据卷信息"""
        self.print_header("导出数据卷信息")

        volumes = self.client.volumes.list()
        if not volumes:
            self.print_info("没有数据卷需要导出")
            return {}

        export_info = {}
        volumes_dir = self.output_dir / "volumes"
        volumes_dir.mkdir(exist_ok=True)

        for volume in volumes:
            try:
                self.print_info(f"正在导出数据卷信息: {volume.name}")

                volume_info = {
                    'name': volume.name,
                    'driver': volume.attrs['Driver'],
                    'mountpoint': volume.attrs['Mountpoint'],
                    'labels': volume.attrs.get('Labels', {}),
                    'options': volume.attrs.get('Options', {})
                }

                config_file = volumes_dir / f"{volume.name}_info.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(volume_info, f, indent=2, ensure_ascii=False)

                self.print_success(f"已导出信息: {volume.name}")
                export_info[volume.name] = volume_info

            except Exception as e:
                self.logger.error(f"导出数据卷 {volume.name} 信息失败: {e}")
                self.print_error(f"导出失败: {volume.name}")

        return export_info

    def backup_all(self, backup_name: Optional[str] = None):
        """
        完整备份所有Docker资源

        Args:
            backup_name: 备份名称
        """
        if backup_name is None:
            backup_name = f"docker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.print_header(f"开始完整备份：{backup_name}")

        # 创建备份目录
        backup_dir = self.output_dir / backup_name
        backup_dir.mkdir(exist_ok=True)

        # 临时修改输出目录
        old_output_dir = self.output_dir
        self.output_dir = backup_dir

        # 备份镜像
        images_info = self.export_images()

        # 备份容器配置
        containers_info = self.export_containers()

        # 备份数据卷信息
        volumes_info = self.export_volumes()

        # 生成备份清单
        manifest = {
            'backup_name': backup_name,
            'backup_time': datetime.now().isoformat(),
            'backup_by': '威软科技 Docker迁移工具',
            'images': images_info,
            'containers': containers_info,
            'volumes': volumes_info,
            'statistics': {
                'total_images': len(images_info),
                'total_containers': len(containers_info),
                'total_volumes': len(volumes_info)
            }
        }

        manifest_file = backup_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # 恢复输出目录
        self.output_dir = old_output_dir

        self.print_header("备份完成")
        self.print_success(f"备份位置: {backup_dir}")
        self.print_info(f"镜像数量: {len(images_info)}")
        self.print_info(f"容器数量: {len(containers_info)}")
        self.print_info(f"数据卷数量: {len(volumes_info)}")

        return manifest

    def restore_from_backup(self, backup_path: str):
        """
        从备份恢复

        Args:
            backup_path: 备份目录路径
        """
        backup_dir = Path(backup_path)

        if not backup_dir.exists():
            self.print_error(f"备份目录不存在: {backup_dir}")
            return

        manifest_file = backup_dir / "manifest.json"
        if not manifest_file.exists():
            self.print_error("未找到备份清单文件")
            return

        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        self.print_header(f"从备份恢复：{manifest['backup_name']}")
        self.print_info(f"备份时间: {manifest['backup_time']}")

        # 恢复镜像
        images_dir = backup_dir / "images"
        if images_dir.exists():
            self.import_images(images_dir)

        # 恢复容器（创建新容器）
        containers_dir = backup_dir / "containers"
        if containers_dir.exists():
            self.print_header("恢复容器")
            self.print_info("注意：容器配置已保存，请手动根据配置文件重新创建容器")
            self.print_info(f"配置文件位置: {containers_dir}")

        # 恢复数据卷
        volumes_dir = backup_dir / "volumes"
        if volumes_dir.exists():
            self.print_header("恢复数据卷")
            self.print_info("注意：数据卷信息已保存，请手动根据信息文件重新创建数据卷")
            self.print_info(f"信息文件位置: {volumes_dir}")

        self.print_header("恢复完成")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Docker迁移工具 - 威软科技',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 列出所有Docker资源
  python docker_migrate.py list

  # 导出所有镜像
  python docker_migrate.py export-images

  # 导出特定镜像
  python docker_migrate.py export-images --images nginx:latest redis:latest

  # 导入镜像
  python docker_migrate.py import-images --dir ./docker_backup/images

  # 完整备份
  python docker_migrate.py backup

  # 从备份恢复
  python docker_migrate.py restore --backup ./docker_backup/docker_backup_20260101_120000

作者：威软科技
        '''
    )

    parser.add_argument(
        'action',
        choices=['list', 'export-images', 'import-images', 'export-containers', 'backup', 'restore'],
        help='要执行的操作'
    )

    parser.add_argument(
        '--output-dir', '-o',
        default='./docker_backup',
        help='输出目录 (默认: ./docker_backup)'
    )

    parser.add_argument(
        '--images',
        nargs='+',
        help='要导出的镜像名称列表'
    )

    parser.add_argument(
        '--containers',
        nargs='+',
        help='要导出的容器名称列表'
    )

    parser.add_argument(
        '--dir',
        help='导入时的源目录'
    )

    parser.add_argument(
        '--backup',
        help='备份目录路径（用于恢复操作）'
    )

    parser.add_argument(
        '--name',
        help='备份名称'
    )

    args = parser.parse_args()

    # 打印工具标题
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         Docker 迁移工具 - 威软科技                       ║")
    print("║         简单 · 可靠 · 易用                               ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    # 创建工具实例
    tool = DockerMigrationTool(output_dir=args.output_dir)

    # 执行操作
    try:
        if args.action == 'list':
            tool.list_resources()

        elif args.action == 'export-images':
            tool.export_images(image_names=args.images)

        elif args.action == 'import-images':
            tool.import_images(images_dir=args.dir)

        elif args.action == 'export-containers':
            tool.export_containers(container_names=args.containers)

        elif args.action == 'backup':
            tool.backup_all(backup_name=args.name)

        elif args.action == 'restore':
            if not args.backup:
                tool.print_error("请使用 --backup 参数指定备份目录")
                sys.exit(1)
            tool.restore_from_backup(args.backup)

        print(f"\n{Colors.GREEN}{Colors.BOLD}操作成功完成！{Colors.END}\n")

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}操作已取消{Colors.END}")
        sys.exit(0)
    except Exception as e:
        tool.logger.error(f"操作失败: {e}")
        tool.print_error(f"操作失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
