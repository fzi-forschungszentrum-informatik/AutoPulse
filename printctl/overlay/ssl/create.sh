#!/bin/sh

source ./.env
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:secp384r1 -days 3650 \
	-nodes -keyout default.key -out default.crt -subj "/CN=$DNS" \
	-addext "subjectAltName=DNS:$DNS,IP:$IP"
