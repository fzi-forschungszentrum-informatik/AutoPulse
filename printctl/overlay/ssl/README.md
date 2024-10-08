# Certificate Creation

This directory contains the script to generate the SSL certificates for the API and the Web interface.
You can also supply your own certificate, if your organisation provides one.

We do not advise exposing the API to the internet, even with SSL and authentication. We supply you with the tools to enable both, as it's best practice to do so, even in local networks.

## Steps to create a self-signed certificate

1. Rename the `preview.env` to `.env` and fill in the required fields.
2. Run the `create.sh` script.
3. With the default settings we applied to traefik, the certificate will automatically be picked up and served, provided you used the command `just init && just start` to set up the stack.
