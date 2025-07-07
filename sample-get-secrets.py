import requests
import os

def main():
    address = os.environ['VAULT_ADDR']
    url = f'{address}/v1/secrets/data/example'
    token = os.environ['VAULT_TOKEN']
    headers =  {"X-Vault-Token": token}
    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response = response.json()
            print(response['data']['data']['password'])
        else:
            print('Error:', response.status_code)

    except requests.exceptions.RequestException as e:
        print('Error:', e)
    
if __name__ == '__main__':
    main()
