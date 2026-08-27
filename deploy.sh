#!/bin/bash
# ─────────────────────────────────────────────
# SEO Agent 部署脚本 (Ubuntu/Debian)
# 用法: bash deploy.sh
# ─────────────────────────────────────────────

set -e

# 1. 安装系统依赖
echo ">>> 安装系统依赖..."
sudo apt update -y
sudo apt install -y python3 python3-pip nginx

# 2. 创建项目目录
APP_DIR="/opt/seo-agent"
echo ">>> 创建项目目录 $APP_DIR..."
sudo mkdir -p $APP_DIR

# 3. 复制代码（假设当前目录就是代码目录）
echo ">>> 复制代码文件..."
sudo cp seo_agent.py seo_report.py seo_web.py seo_wsgi.py requirements.txt $APP_DIR/

# 4. 安装 Python 依赖
echo ">>> 安装 Python 依赖..."
cd $APP_DIR
sudo pip3 install -r requirements.txt

# 5. 配置 gunicorn systemd 服务
echo ">>> 配置 systemd 服务..."
sudo tee /etc/systemd/system/seo-agent.service > /dev/null <<'EOF'
[Unit]
Description=SEO Analysis Agent
After=network.target

[Service]
User=root
WorkingDirectory=/opt/seo-agent
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:8888 seo_wsgi:app --timeout 60
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable seo-agent
sudo systemctl start seo-agent
echo ">>> gunicorn 服务已启动"

# 6. 配置 Nginx 反向代理
echo ">>> 配置 Nginx..."
sudo tee /etc/nginx/conf.d/seo-agent.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;  # 替换为你的域名

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 90;
    }
}
EOF

sudo nginx -t
sudo systemctl reload nginx
echo ">>> Nginx 配置完成"

# 7. 检查状态
echo ""
echo "──────────────────────────────────"
echo "  部署完成!"
echo "──────────────────────────────────"
echo "  本地测试: curl http://localhost:8888"
echo "  公网访问: http://你的服务器IP"
echo ""
echo "  下一步:"
echo "  1. 绑定域名: 修改 /etc/nginx/conf.d/seo-agent.conf 中的 server_name"
echo "  2. 配置 HTTPS: sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx"
echo "  3. 管理服务: sudo systemctl status|restart|stop seo-agent"
echo "──────────────────────────────────"
