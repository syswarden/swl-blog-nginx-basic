#!/bin/bash

# settings

declare -A SETTINGS=(
    [SSH_PORT]=''
    [CONTROL_PORT]=''
    
    [SSL_DOMAIN]=''
    [AUTOMATE_DOMAIN]=''

    [AUTOMATE_INTERNAL_IP]=''
    [WHITELIST_EXTERNAL_IP]=''

    [SSL_NOTIFICTION_EMAIL]=''
    [SSL_CLOUDFLARE_EMAIL]=''
    [SSL_CLOUDFLARE_APIKEY]=''
    
    [SSL_INTERNAL_COUNTRY]=''
    [SSL_INTERNAL_STATE]=''
    [SSL_INTERNAL_CITY]=''
    [SSL_INTERNAL_COMPANY]=''
)

# remove ufw

ufw reset
ufw disable
apt remove ufw -y

# configure repositories

add-apt-repository universe -y
add-apt-repository ppa:certbot/certbot -y
curl https://nginx.org/keys/nginx_signing.key | apt-key add -
cp settings/etc/apt/sources.list.d/nginx.list /etc/apt/sources.list.d/nginx.list

# update apt cache

DEBIAN_FRONTEND=noninteractive apt-get update

# install packages

ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive apt-get install -y \
  nginx \
  certbot  \
  openssh-server \
  iptables-persistent \
  software-properties-common \
  python3-certbot-dns-cloudflare

# copy and update the template files

TEMPLATE_PATH=$(date +%s)

mkdir -p $TEMPLATE_PATH

rsync -rvi templates/ $TEMPLATE_PATH/

for TEMPLATE_FILE in $(find $TEMPLATE_PATH -type f); do
    for SETTING in "${!SETTINGS[@]}"; do
        sed -i "s/{{$SETTING}}/${SETTINGS[$SETTING]}/g" $TEMPLATE_FILE
    done
done

# copy the the generated template files

rsync -rvi $TEMPLATE_PATH/etc/ /etc/

# generate external ssl cert

certbot certonly -d "*.${SETTINGS[SSL_EXTERNAL_DOMAIN]}"

# generate internal ssl cert

SSL_INTERNAL_CNF='/etc/letsencrypt/internal/internal-cert.cnf'
SSL_INTERNAL_KEY='/etc/letsencrypt/internal/internal-cert.key'
SSL_INTERNAL_CSR='/etc/letsencrypt/internal/internal-cert.csr'
SSL_INTERNAL_CRT='/etc/letsencrypt/internal/internal-cert.crt'
SSL_INTERNAL_PFX='/etc/letsencrypt/internal/internal-cert.pfx'

openssl genrsa -out $SSL_INTERNAL_KEY 2048

openssl req -new -out $SSL_INTERNAL_CSR -key $SSL_INTERNAL_KEY -config $SSL_INTERNAL_CNF

openssl x509 -req -days 9125 -in $SSL_INTERNAL_CSR -signkey $SSL_INTERNAL_KEY -out $SSL_INTERNAL_CRT -extensions v3_req -extfile $SSL_INTERNAL_CNF

openssl pkcs12 -inkey $SSL_INTERNAL_KEY -in $SSL_INTERNAL_CRT -export -out $SSL_INTERNAL_PFX

# generate nginx dhparam

openssl dhparam -out /etc/nginx/custom/dhparam.pem 4096


