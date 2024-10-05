import requests
import qrcode

import credentials

api_key = credentials.get_secret("blockonomics-api-key")
url = 'https://www.blockonomics.co/api/new_address'
headers = {'Authorization': 'Bearer ' + api_key}
payment_data = {
    'price': 0.01,
    'currency': 'BTC',
}
def request():
    r = requests.post(url, headers=headers, json=payment_data)

    # Prüfen, ob die Adresse erfolgreich erstellt wurde
    if r.status_code == 200:
        address = r.json()['address']
        # print('Payment receiving address: ' + address)
        return payment_data['price'], address

    else:
        print(r.status_code, r.text)


def get_total_btc_received(addresses):
    total_balance = 0.000
    for address in addresses:
        if not address:
            continue

        response = requests.get(f"{url}/{address}", headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
                if 'balance' in data:
                    total_balance += float(data['balance'])
            except ValueError:
                pass
    return total_balance


def generate_qr_code(bitcoin_address):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    bitcoin_uri = f'bitcoin:{bitcoin_address}'
    qr.add_data(bitcoin_uri)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    qr_file = f'{bitcoin_address}.png'
    img.save(qr_file)
    return qr_file

