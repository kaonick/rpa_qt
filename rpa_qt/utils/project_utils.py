import uuid
import urllib.request
from rpa_qt.utils.time_utils import get_now_code


def get_case_code():
    case=get_now_code()+"_"+uuid.uuid4().hex[:10]
    return case


def save_image(url,path):
    try:
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as err:
        print(f"Error:{err}")
        return False


def url2file_name(url: str):
    # file_name = "".join(i for i in title if i not in "\/:*?<>|")
    file_name = url.split('//')[-1].replace('/', '_').replace('.', '_').replace('#','_').replace(':','_')
    file_name = file_name.split('?')[0]
    return file_name


def crawl_logo(url):
    print(f"crawl_logo url={url}")

    # if url=="https://ec.elifemall.com.tw":
    #     pass

    from urllib.request import urlopen,Request
    from bs4 import BeautifulSoup
    # htmldata = urlopen('https://en.wikipedia.org/wiki/Pepsi')

    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    htmldata = urlopen(req).read()


    # htmldata = urlopen(url)

    soup = BeautifulSoup(htmldata, 'html.parser')
    images = soup.find_all('img')

    urls=[]
    for item in images:
        if 'src' in item.attrs:
            img = 'https:' + item['src']

        if "data-src" in item.attrs:
            img = 'https:' + item['data-src']

        # img = 'https:' + item['src']
        # print(img)
        if 'logo' in img:
            print(img)
            urls.append(img)
    return urls


def get_free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return str(port)

if __name__ == '__main__':
    # crawl_logo()
    print(get_free_port())
