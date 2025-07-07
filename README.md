Hashicorp vault is a secrets management tool used to store, secure and manage secrets such as passwords, tokens, keys, etc. It provides a centralized and secured way to protect credentials. To learn about vault visit [official docs](https://developer.hashicorp.com/vault/docs).

# Setting Up a Vault Server

## Installation
Install using package manager or specific binaries depending on OS distribution by following [install doc](https://developer.hashicorp.com/vault/install).

For example, on Rocky:

```
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
sudo dnf -y install vault
```

Alternatively, download the latest version of vault binary from [vault releases](https://releases.hashicorp.com/vault/?ref=devopscube.com). 

Then copy the binary to /usr/bin.

```
sudo cp vault /usr/bin/
```
## Configuration
Create configuration directory under /etc, a vault data directory and logs directory.
```
sudo mkdir /etc/vault
sudo mkdir /vault-data
sudo mkdir -p /logs/vault/
```
Create `/etc/vault/config.json` and add the following vault configuration:

```
{
"listener": [{
"tcp": {
"address" : "{address}:8200",
"tls_disable" : 1
}
}],
"api_addr": "http://{address}:8200",
"storage": {
    "file": {
    "path" : "/vault-data"
    }
 },
"max_lease_ttl": "10h",
"default_lease_ttl": "10h",
"ui":true
}
```
Replace {address} with your host IP.

Note that vault supports both JSON and HCL formats.

Configuration in HCL, `config.hcl`:
```
listener "tcp" {
  address     = "{address}:8200"
  tls_disable = 1
}

api_addr = "http://{address}:8200"
storage "file" {
  path = "./vault-data"
}
max_lease_ttl = "10h"
default_lease_ttl = "10h"
ui = true
```
### Breaking down the configuration
- **listener** parameter configures how server listens to API requests. 
- **api_addr**: URL for client API calls.
- **storage**: The storage backend configuration. Here the storage backend is a filesystem where data is stored in the specified path. Vault server is the only component that interacts with the backend storage.
- **max_lease_ttl**: Maximum token time to live. The token is invalid after this lease duration.
- **default_lease_ttl**: Deafult token lease duration.
- **ui**: Enables the web UI that is accessed at listener /ui path, http://{address}:{port}/ui.

Tokens are the main client authentication method. For security it must be limited to a time until which it is valid to decrease the chance of attack. By default, it is valid for 32 days. We set a time of 10h to shorten the lease duration and it can be changed as needed. The ttl assigned to a token is the shortest time configured at any configuration level.

**Vault can operate in developement and production modes. We'll walk through both.**
## Developement Server
Vault developement server is a preconfigured local server that is used for testing, stores data in memory and is not very secure. The vault is automically unsealed (we'll have glimpse on sealing later).

To start the server run:
```
vault server -dev
```
This will run the server foreground and another terminal will be needed to run commands.

The unseal key and root token will show as part of the output. They need to be saved and as it is a dev server securing them is not that critical.
```
Unseal Key: SdWOcn7vue+ZrRSdKQ0JhCsjwYnoCNHABFCJgsJQ1zo=
Root Token: hvs.6yhtmz1K74M4e7CTFuSroPSa
```

Also the output will provide the address to configure for client to communicate with the dev server. The provided command should be run. 
```
You may need to set the following environment variables:
                                                                               
    $ export VAULT_ADDR='http://127.0.0.1:8200'
```

Set also VAULT_DEV_ROOT_TOKEN_ID env variable to the root token.
```
export VAULT_DEV_ROOT_TOKEN_ID='hvs.6yhtmz1K74M4e7CTFuSroPSa'
```

Check the server state to test it is running successfully. If successful, the output should be like this:
```
$ vault status
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    1
Threshold       1
Version         1.20.0
Build Date      2025-06-23T10:21:30Z
Storage Type    inmem
Cluster Name    vault-cluster-f389d79b
Cluster ID      3a3f1c2e-9739-841c-6e61-b24475c55bdc
HA Enabled      false
```
Notice from the output the vault is unsealed.

## Production Server

### Unsealing
Before getting into running production server lets have a brief idea about vault unsealing,

Vault uses a sequece of ecryption processes to protect the data in storage. The data is encrypted by an ecryption key. The encryption key itself is encrypted by another key called root key. This root key is encrypted as well. The root key needs the unseal keys by which it was encrypted to be able to decrypt the data ecncryption key. At the end vault cannot decrypt the data when it is in a sealed state. So the unseal keys are needed to be able to do so. Upon successful unsealing vault can access and decrypt this data after the authentication process.

Default vault configuration uses an algorithm to share the key called **Shamir Secret Sharing**. It splits the key into shares which are portions that can be stored in multiple secure places.

The command used to unseal the key is ```vault operator unseal```. It must be run multiple times using multiple unseal keys where each run takes one key as an argument. There are minumum number of keys needed to successfully unseal the vault and the other keys are spare. If keys were lost that the minumum is not satisfied the vault will no longer be accessible either by the attacker or the admins so they are very critical.

### Starting the server
After installing vault and writing configuation, we need to create vault.service to run in the background and start on boot.

Add the following in `/etc/systemd/system/vault.service`:
```
[Unit]
Description=vault service
Requires=network-online.target
After=network-online.target
ConditionFileNotEmpty=/etc/vault/config.json

[Service]
EnvironmentFile=-/etc/sysconfig/vault
Restart=on-failure
ExecStart=/usr/bin/vault server -config=/etc/vault/config.json
StandardOutput=/logs/vault/output.log
StandardError=/logs/vault/error.log
LimitMEMLOCK=infinity
ExecReload=/bin/kill -HUP $MAINPID
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
```

Start and enable the service
```
sudo systemctl enable --now vault.service
```

Set and export the environment variable and let it be set on boot. Replace address with the listener IP.
```
export VAULT_ADDR=http://{address}:8200
echo "export VAULT_ADDR=http://{address}:8200" >> ~/.bashrc
```

As root run the following to initiate the server.
```
vault operator init
```

***Store the output of the previous command as it contains the unseal keys and root token. Generally, they should be distributed and secured.***

The ouput will contain keys that look like this:
```
Unseal Key 1: S0q8VapyPzis8lVzibmM7q4J3EMyk/wBA6iGdzTviXeN
Unseal Key 2: MyJKEz0tXrKVQBuJXlAJY0yIiTJyd9pXhVT0O+2a3Kzz
Unseal Key 3: 9EG/+alO41T2tEC4dwz2hh7MC/99tIsdXg06b8M6PvMb
Unseal Key 4: hdoSsJQA0rEk0j0Hr/EjPafer4bkQ1kyq/6GOIRgjkXX
Unseal Key 5: 1x+xEzEmcMncGXR3h6+1swBvA7afdUXbNyjMVKeR70ie

Initial Root Token: hvs.qzfDsxphk1xjsBTKl5nRgKQU
```

When running vault status it will show that it is sealed.

Use the unseal commands with any 3 of the 5 unseal keys.
```
vault operator unseal S0q8VapyPzis8lVzibmM7q4J3EMyk/wBA6iGdzTviXeN
vault operator unseal MyJKEz0tXrKVQBuJXlAJY0yIiTJyd9pXhVT0O+2a3Kzz
vault operator unseal hdoSsJQA0rEk0j0Hr/EjPafer4bkQ1kyq/6GOIRgjkXX
```

Check vault status
```
vault status
```
Note: make sure to open 8200 port on firewall for client access outside.

```
sudo firewalld-cmd --add-port=8200/tcp --permanent
sudo firewalld-cmd --reload
```
**Now you can login to UI at *http://{address}:8200/ui* with the root token.**

![vault-login](https://github.com/user-attachments/assets/8bc6021e-840d-4a7e-9cf8-d11870dd8e7f)


![vault-root-home](https://github.com/user-attachments/assets/55efefc6-5b10-4778-bd3a-435f8e387fd1)

To login from cli:
```
vault login -method=token
```
This will store the token in **./.vault-token**.

Read more about authentication methods to understand **-method=token** and other methods to use.

# Working with secrets
To store a secret a secret engine must be enabled. Secrets engines manupilate and encrypt data. When initializing a server a pre-enabled engine is provided.

Run `vault secrets list` to check enabled secret engines. The shown output contains the initial secrets engine of path cubbyhole/.
```
$ vault secrets list
Path          Type         Accessor              Description
----          ----         --------              -----------
cubbyhole/    cubbyhole    cubbyhole_867ceffd    per-token private secret storage
identity/     identity     identity_5c6f616f     identity store
sys/          system       system_f4a65c0b       system endpoints used for control, policy and debugging

```
**Note: Vault keeps track of secrets by paths. Everything in Vault is organized and accessed by paths.**

There are several types of secrets. We will enable an engine for key-value secrets using key/vaule plugin version 2 through CLI. It could be done using UI as well.
```
vault secrets enable -path secrets -version 2 kv
```
```
$ vault secrets list
Path          Type         Accessor              Description
----          ----         --------              -----------
cubbyhole/    cubbyhole    cubbyhole_867ceffd    per-token private secret storage
identity/     identity     identity_5c6f616f     identity store
secrets/      kv           kv_daaa3555           n/a
sys/          system       system_f4a65c0b       system endpoints used for control, policy and debugging
```
When a secret engine is enabled a mountpoint is created at which secrets are saved and it is part of the path. By default, its name is the same as of the engine. kv plugin has dedicated commands in the CLI so we'll use it to add new secrets.
```
vault kv put -mount secrets example name=name password=password
```

View added secrets,
```
$ vault kv list secrets
Keys
----
example

$ vault kv get -mount secrets example                                 
==== Secret Path ====
secrets/data/example    
                                       
======= Metadata =======
Key                Value                                                       
---                -----
created_time       2025-07-07T17:34:03.839440264Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            2
                                       
====== Data ======
Key         Value   
---         -----
password    password
username    name
```

Another way to get the secret data via CLI is `vault kv get secrets/example`.

The output shows the full secret path, metadata and secret data. This data along with the API and CLI paths can be shown in the UI and will be useful when testing with API calls to these endpoints. The varsion shown in Metadata is 2 as the secret was modified. This is a featre in version 2 of kv plugin which is versioning.

# Authentication
To enable user authentication to login with username and password userpass plugin can be used by enabling userpass authentication method.
```
vault auth enable userpass
```
Create new user.
```
$ vault write auth/userpass/users/admin password=password
Success! Data written to: auth/userpass/users/admin
```


# Create and Attach Policy
It is worth highlighting that root token is recommended to be used as minimal as possible as it has full access. So to avoid root we will continue with user access instead. We'll need to create a new policy to give it access to the needed secrets.
## Create Policy 
Create policy for the secrets/example data,
```
$ vault policy write secrets-example-policy - << EOF
path "secrets/data/example" {
   capabilities = ["read", "create", "update", "delete"]
}
EOF
Success! Uploaded policy: secrets-example-policy
```
## Attach Policy to User

```
$ vault write auth/userpass/users/admin policies=secrets-example-policy
Success! Data written to: auth/userpass/users/admin
```

## Testing 
On login, a new token is generated for this user and overrides ~/.vault-token content.
```
$ vault login -method=userpass username=admin
Password (will be hidden): 
Success! You are now authenticated. The token information displayed below
is already stored in the token helper. You do NOT need to run "vault login"
again. Future Vault requests will automatically use this token.

Key                    Value
---                    -----
token                  hvs.CAESIBqWq07o_PColirprXJFRutpNbe7XTRCcnBvVU35UswsGh4KHGh2cy5JcHVqYm04b0lLOGxmOGJjZVpOTURvYWQ
token_accessor         fW7CLlG59dU2GDSDxvsobheX
token_duration         10h
token_renewable        true
token_policies         ["default"]
identity_policies      []
policies               ["default"]
token_meta_username    admin


$ vault kv get -mount secrets example
==== Secret Path ====
secrets/data/example

======= Metadata =======
Key                Value
---                -----
created_time       2025-07-07T18:13:17.526871847Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            5

====== Data ======
Key         Value
---         -----
password    password
username    name

```

# Testing Endpoints via API
Secrets can either be retrieved from UI, CLI or API calls. We can use path shown in the secrets path on UI to make API calls.

![paths](https://github.com/user-attachments/assets/6fa70045-bab8-4055-9605-7f4825946b39)

Retrieve the secret in json format as follows:
```
$ VAULT_TOKEN=`cat ~/.vault-token`
$ curl -H "X-Vault-Token:${VAULT_TOKEN}" -X GET http://192.168.56.144:8200/v1/secrets/data/example --silent | jq ".data.data"
{
  "password": "password",
  "username": "name"
}

```

sample-get-secrets.py is a sample test to retrieve secrets with API calls from a python script. The script uses VAULT_ADDR and VAULT_TOKEN env variables values to make call to /secrets/data/db-secrets' and get the password credential.

set VAULT_TOKEN environment variable before running the script if not set.
```
$ export VAULT_TOKEN=`cat ~/.vault-token`
$ python3 sample-get-secrets.py
password
```

# References
- https://developer.hashicorp.com/vault/docs
- https://developer.hashicorp.com/vault/tutorials/get-started/setup
- https://developer.hashicorp.com/vault/docs/get-started/operations-qs
- https://devopscube.com/setup-hashicorp-vault-beginners-guide/
- https://medium.com/@martin.hodges/vault-secrets-engines-paths-and-roles-explained-aa3e1a84037d
