"""
透過@botfather建立bot，例如@Taiwanno1bot，就會拿到：token

在@Taiwanno1bot，將user加入， 例如：@kaonick /start
然後在web中輸入：https://api.telegram.org/bot{token}}/getUpdates
就會顯示 chat_id

"""
import requests

# request to send a message to a telegram chat
def send_message(chat_id, message, token):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    proxies = {
        "http": "http://n000000930:20251Kaonick@tpisa:80",
        "https": "http://n000000930:20251Kaonick@tpisa:80",
    }

    # response = requests.post(url, data=data, proxies=proxies)
    response = requests.post(url, data=data)
    # proxies={"http": "http://N000000930:20251Kaonick@10.3.3.109:80","https": "http://N000000930:20251Kaonick@10.3.3.109:80"}

    return response.json()



if __name__ == '__main__':
    chat_id = "265592581"
    message = "Hello, World!今年要賺500萬"
    token = "244257890:AAE1eclNmacL2IwKclzRZTiBnWSf3tLgmkI"
    send_message(chat_id, message, token)