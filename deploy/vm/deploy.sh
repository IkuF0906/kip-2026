#!/bin/sh
# GitHub Actions が SSH で呼ぶデプロイ用スクリプト。VM の /opt/drill/deploy.sh に置く。
# デプロイ用の鍵は authorized_keys の command= でこのスクリプトしか実行できないようにしてあり、
# ssh で送ったコマンド（コミットのハッシュ）は SSH_ORIGINAL_COMMAND に入る。
set -eu

sha="${SSH_ORIGINAL_COMMAND:-${1:-}}"
case "$sha" in
  *[!0-9a-f]* | "") echo "コミットのハッシュ（40文字の16進数）を渡してください" >&2; exit 2 ;;
esac
[ "${#sha}" -eq 40 ] || { echo "コミットのハッシュは40文字です" >&2; exit 2; }

# GitHub ではフォークのコミットも元のリポジトリの URL で取得できてしまう。
# 他人が書いた compose.prod.yaml で動かされないよう、main に含まれるコミットだけを受け付ける
body=$(curl -fsS "https://api.github.com/repos/IkuF0906/kip-2026/compare/$sha...main") || {
  echo "main に含まれるコミットか確かめられませんでした" >&2
  exit 3
}
# 一番外側の "status"（identical: main と同じ、ahead: main のほうが進んでいる）
status=$(printf '%s\n' "$body" | sed -n 's/^  "status": "\([a-z]*\)",$/\1/p')
case "$status" in
  identical | ahead) ;;
  *) echo "main に含まれないコミットです（$status）" >&2; exit 3 ;;
esac

cd /opt/drill
# 構成はそのコミットの deploy/compose.prod.yaml を使う（リポジトリは公開なので認証は要らない）
curl -fsSL "https://raw.githubusercontent.com/IkuF0906/kip-2026/$sha/deploy/compose.prod.yaml" -o compose.yaml.new
mv compose.yaml.new compose.yaml
echo "IMAGE_TAG=$sha" > .env

docker compose pull -q app nginx
docker compose up -d --remove-orphans

# 新しい版が応答するまで待つ
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8080/api/version 2>/dev/null | grep -q "$sha"; then
    docker image prune -f >/dev/null
    echo "デプロイしました: $sha"
    exit 0
  fi
  sleep 2
done
echo "新しい版が応答しません" >&2
docker compose ps >&2
exit 1
