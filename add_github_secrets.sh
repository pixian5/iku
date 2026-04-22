#!/bin/bash
# GitHub Secrets 添加工具
# 用于自动添加环境变量到 GitHub 仓库
# 用法: ./add_github_secrets.sh <GITHUB_TOKEN> <REPO> <SECRET_NAME> <SECRET_VALUE>

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ "$#" -lt 4 ]; then
    echo -e "${YELLOW}用法:${NC}"
    echo "  $0 <GITHUB_TOKEN> <REPO> <SECRET_NAME> <SECRET_VALUE>"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 ghp_xxxx pixian5/iku USERNAME myuser"
    echo "  $0 ghp_xxxx pixian5/iku PASSWORD mypass"
    echo ""
    echo -e "${YELLOW}批量添加（从.env文件）:${NC}"
    echo "  $0 ghp_xxxx pixian5/iku --env-file .env"
    echo ""
    echo -e "${YELLOW}Token权限要求:${NC}"
    echo "  需要 repo 和 workflow 权限"
    exit 1
fi

TOKEN="$1"
REPO="$2"

# 检查加密工具
setup_crypto_env() {
    if [ ! -d /tmp/crypto_env ]; then
        echo -e "${YELLOW}正在安装加密工具...${NC}"
        python3 -m venv /tmp/crypto_env
        source /tmp/crypto_env/bin/activate
        pip install pynacl requests -q
        deactivate
    fi
}

# 获取仓库公钥
get_public_key() {
    local response
    response=$(curl -s -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/secrets/public-key")

    KEY_ID=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['key_id'])")
    PUBLIC_KEY=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])")

    if [ -z "$KEY_ID" ] || [ -z "$PUBLIC_KEY" ]; then
        echo -e "${RED}错误: 无法获取仓库公钥，请检查Token权限和仓库名${NC}"
        exit 1
    fi
}

# 添加单个Secret
add_secret() {
    local name="$1"
    local value="$2"

    local result
    result=$(/tmp/crypto_env/bin/python3 << EOF
import base64
import requests
from nacl import encoding, public

PUBLIC_KEY = "$PUBLIC_KEY"
KEY_ID = "$KEY_ID"
TOKEN = "$TOKEN"
REPO = "$REPO"
SECRET_NAME = "$name"
SECRET_VALUE = "$value"

def encrypt_secret(public_key_b64, secret_value):
    public_key_bytes = base64.b64decode(public_key_b64)
    public_key = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

encrypted_value = encrypt_secret(PUBLIC_KEY, SECRET_VALUE)
url = f"https://api.github.com/repos/{REPO}/actions/secrets/{SECRET_NAME}"
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
data = {
    "encrypted_value": encrypted_value,
    "key_id": KEY_ID
}
response = requests.put(url, headers=headers, json=data)
print(response.status_code)
EOF
)

    if [ "$result" = "201" ] || [ "$result" = "204" ]; then
        echo -e "${GREEN}✅ $name 添加成功${NC}"
        return 0
    else
        echo -e "${RED}❌ $name 添加失败 (HTTP $result)${NC}"
        return 1
    fi
}

# 从.env文件批量添加
add_from_env_file() {
    local env_file="$1"

    if [ ! -f "$env_file" ]; then
        echo -e "${RED}错误: 文件 $env_file 不存在${NC}"
        exit 1
    fi

    echo -e "${YELLOW}从 $env_file 批量添加 Secrets...${NC}"
    echo ""

    while IFS='=' read -r name value || [ -n "$name" ]; do
        # 跳过空行和注释
        [ -z "$name" ] && continue
        [[ "$name" =~ ^# ]] && continue

        # 去除前后空格
        name=$(echo "$name" | xargs)
        value=$(echo "$value" | xargs)

        [ -z "$name" ] && continue

        add_secret "$name" "$value"
    done < "$env_file"
}

# 列出现有Secrets
list_secrets() {
    echo -e "${YELLOW}现有 Secrets:${NC}"
    curl -s -H "Authorization: token $TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$REPO/actions/secrets" | \
        python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  - {s[\"name\"]}') for s in d.get('secrets',[])]"
}

# 主流程
main() {
    setup_crypto_env
    get_public_key

    # 批量模式
    if [ "$3" = "--env-file" ]; then
        add_from_env_file "$4"
        echo ""
        list_secrets
        exit 0
    fi

    # 单个添加模式
    local SECRET_NAME="$3"
    local SECRET_VALUE="$4"

    echo -e "${YELLOW}添加 Secret 到 $REPO...${NC}"
    add_secret "$SECRET_NAME" "$SECRET_VALUE"
    echo ""
    list_secrets
}

main
