import os
import hvac

def main():
    address = os.environ['VAULT_ADDR']
    try:
        client = hvac.Client(address)
        response = client.secrets.kv.read_secret_version(path='example', mount_point='secrets', raise_on_deleted_version=False)
        print(response['data']['data']['password'])

    except hvac.exceptions.VaultError as vaulterror:
          print(vaulterror)
    
if __name__ == '__main__':
    main()
