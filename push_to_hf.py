#!/usr/bin/env python3
"""一键推送 SEO Agent 到 Hugging Face Spaces

用法:
    python push_to_hf.py
    然后输入你的 HF 用户名和 Token
"""

import os
import sys
import shutil
import subprocess

HF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "huggingface")
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_deploy_tmp")

def run(cmd, cwd=None):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return False
    if result.stdout.strip():
        print(f"  {result.stdout.strip()}")
    return True

def main():
    print("=" * 50)
    print("  Hugging Face Spaces 部署工具")
    print("=" * 50)
    print()

    username = input("Hugging Face 用户名: ").strip()
    if not username:
        print("用户名不能为空")
        return

    token = input("Hugging Face Token (粘贴): ").strip()
    if not token:
        print("Token 不能为空")
        return

    space_name = "seo-agent"
    repo_url = f"https://{username}:{token}@huggingface.co/spaces/{username}/{space_name}"

    print()
    print(f"目标: https://huggingface.co/spaces/{username}/{space_name}")
    print()

    # 清理临时目录
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    # 克隆空仓库
    print("[1/5] 克隆 Hugging Face 仓库...")
    if not run(f'git clone "https://huggingface.co/spaces/{username}/{space_name}" "{TEMP_DIR}"'):
        # 仓库可能不存在，创建空目录
        print("  仓库不存在或为空，直接初始化...")
        os.makedirs(TEMP_DIR, exist_ok=True)

    # 复制文件
    print("[2/5] 复制项目文件...")
    for f in os.listdir(HF_DIR):
        src = os.path.join(HF_DIR, f)
        dst = os.path.join(TEMP_DIR, f)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  复制: {f}")
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
            print(f"  复制目录: {f}")

    # Git 初始化和提交
    print("[3/5] 初始化 Git 仓库...")
    run("git init", cwd=TEMP_DIR)
    run("git add -A", cwd=TEMP_DIR)
    run('git commit -m "SEO Analysis Agent - Gradio App"', cwd=TEMP_DIR)
    run("git branch -M main", cwd=TEMP_DIR)

    # 推送
    print("[4/5] 推送到 Hugging Face...")
    run(f'git remote add origin "{repo_url}"', cwd=TEMP_DIR)
    if not run("git push -u origin main --force", cwd=TEMP_DIR):
        print("\n推送失败！请检查:")
        print(f"  1. 用户名是否正确: {username}")
        print("  2. Token 是否有 Write 权限")
        print("  3. 是否已创建 Space: https://huggingface.co/new-space")
        print(f"     Space 名称必须是: {space_name}")
        return

    # 清理
    print("[5/5] 清理临时文件...")
    shutil.rmtree(TEMP_DIR)

    print()
    print("=" * 50)
    print("  部署成功!")
    print("=" * 50)
    print()
    print(f"  访问地址: https://{username}-{space_name}.hf.space")
    print(f"  管理页面: https://huggingface.co/spaces/{username}/{space_name}")
    print()
    print("  首次构建需要 2-3 分钟，请耐心等待。")
    print("  如果 Token 出现在 git log 中，建议在 HF 设置中重新生成 Token。")

if __name__ == "__main__":
    main()
