# 画面（static/）を配信し、/api/ をアプリに転送する nginx のイメージ。ビルドはリポジトリの直下から行う
FROM nginx:1.27-alpine

COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY static/ /usr/share/nginx/html/
