[*.athenagu.com]


listen 80;
listen 443 ssl;

server_name tools.athenagu.com;

ssl_certificate /etc/letsencrypt/live/jinns.top/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/jinns.top/privkey.pem;
ssl_session_timeout 5m;
ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
ssl_ciphers AESGCM:ALL:!DH:!EXPORT:!RC4:+HIGH:!MEDIUM:!LOW:!aNULL:!eNULL;
ssl_prefer_server_ciphers on;

