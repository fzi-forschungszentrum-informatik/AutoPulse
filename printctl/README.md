# Printer Control

We use the excellent [mkuf/prind](https://github.com/mkuf/prind) to control our printer.
Before you can start the stack, we apply an overlay to add SSL and Basic Authentication to the API and Web interface.

## Initial setup

This is a one-time setup, and you can skip this step if you have already done it.
This will clone the repository and add our overlay.
We've pinned the version to ensure compatibility.
If you need an up-to-date version, you need to manually confirm that our settings still apply.

```sh
just init
```

## Add Basic Authentication

We use the `.env` file to set the API and Web interface credentials.
Use the `htpasswd` command to generate the password hash.

```sh
echo -n 'PI_USER_PASS=' > prind/.env
echo $(htpasswd -nB pi) | sed -e s/\\$/\\$\\$/g >> prind/.env
```

This will add the user `pi` with the password you supplied.

## Start the stack

```sh
just start
```
