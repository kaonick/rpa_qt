



# query binance price SOLUSDT
import requests
def price_pair(currency_pair: str) -> float:
    """
    Query the current price of a cryptocurrency pair from Binance.

    :param currency_pair: The trading pair symbol (e.g., 'BTCUSDT').
    :return: The current price of the specified trading pair.
    """
    url = f'https://api3.binance.com/api/v3/ticker/price?symbol={currency_pair}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(f"Current price of {currency_pair}: {data['price']}")
        return float(data['price'])
    else:
        raise Exception(f"Error fetching price for {currency_pair}: {response.status_code} - {response.text}")


if __name__ == '__main__':
    price_pair("SOLUSDT")