#!/bin/bash
# 设置Podman私有Registry脚本
# 女娲造物：以容器为界，隔离天地

set -e

echo "🔨 女娲开始构建私有容器仓库..."

# 创建registry目录
mkdir -p ~/text2sql-mvp0/registry/{data,certs,auth}

# 生成自签名证书
echo "🔐 铸造安全符印..."
cd ~/text2sql-mvp0/registry/certs
openssl req -newkey rsa:4096 -nodes -sha256 -keyout domain.key \
  -x509 -days 365 -out domain.crt \
  -subj "/C=CN/ST=Digital/L=Cloud/O=Text2SQL/CN=registry.text2sql.local"

# 创建基本认证
echo "🗝️ 设置访问密钥..."
podman run --rm --entrypoint htpasswd httpd:2 -Bbn text2sql secure123 > ~/text2sql-mvp0/registry/auth/htpasswd

# 启动registry容器
echo "🏗️ 召唤容器守护神..."
podman run -d \
  --name text2sql-registry \
  -p 5000:5000 \
  -v ~/text2sql-mvp0/registry/data:/var/lib/registry:z \
  -v ~/text2sql-mvp0/registry/certs:/certs:z \
  -v ~/text2sql-mvp0/registry/auth:/auth:z \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  -e REGISTRY_AUTH=htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_REALM="Registry Realm" \
  docker.io/library/registry:2

# 添加到系统信任
echo "🌟 将符印刻入信任之石..."
sudo cp ~/text2sql-mvp0/registry/certs/domain.crt /etc/pki/ca-trust/source/anchors/text2sql-registry.crt
sudo update-ca-trust

# 配置Podman信任此registry
mkdir -p ~/.config/containers/
cat > ~/.config/containers/registries.conf << EOF
[[registry]]
location = "localhost:5000"
insecure = false
EOF

echo "✨ 私有容器仓库构建完成！"
echo "📋 使用方法："
echo "   podman login localhost:5000 -u text2sql -p secure123"
echo "   podman tag your-image localhost:5000/your-image:tag"
echo "   podman push localhost:5000/your-image:tag"