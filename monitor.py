import socket
import ssl
import sys
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser
import warnings

def parse_url(url):
    parsed_url = urlparse(url)
    protocol = parsed_url.scheme
    host = parsed_url.netloc
    path = parsed_url.path if parsed_url.path else '/'
    return protocol, host, path

def establish_tcp_connection(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=5)
        return sock
    except Exception as e:
        print(f'Network Error:\n {e}')
        return None

def construct_http_request(host, path):
    request = f'GET {path} HTTP/1.0\r\n'
    request += f'Host: {host}\r\n'
    request += '\r\n'
    return request

def analyze_http_response(response):
    try:
        status_line = response.split(b'\r\n', 1)[0].decode('utf-8')
        status_code = int(status_line.split(' ')[1])
        status_message = status_line.split(' ', 2)[2]
        
        return status_code, status_message
    except Exception as e:
        print(f'Error analyzing HTTP response: {e}')
        return None

def fetch_url(url):
    protocol, host, path = parse_url(url)
    
    port = 80 if protocol == 'http' else 443
    
    sock = establish_tcp_connection(host, port)
    
    if not sock:
        return
    
    if protocol == 'https':
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            sock = context.wrap_socket(sock, server_hostname=host)

    request = construct_http_request(host, path)

    try:
        sock.sendall(request.encode('utf-8'))
    except Exception as e:
        print(f'Error sending HTTP request: {e}')
        sock.close()
        return

    response = b''
    while True:
        data = sock.recv(4096)
        if not data:
            break
        response += data

    status_code, status_message = analyze_http_response(response)
    
    if status_code is not None:    # print info if present
        print(f'URL: {url}\nStatus: {status_code} {status_message}')
    

    if status_code in [301, 302]:
        redirected_url = get_redirected_url(response)
        print(f'Redirected URL: {redirected_url}')
        fetch_url(redirected_url)

    if status_code // 100 == 2:  # 2xx status code
        fetch_referenced_objects(response)

    sock.close()

def get_redirected_url(response):
    location_line = response.split(b'\r\n', 2)[1]
    location = location_line.split(b': ')[1].decode('utf-8')
    return location

def fetch_referenced_objects(response):
    pass

def main():
    if len(sys.argv) != 2:
        print('Usage: monitor urls_file')
        sys.exit()

    urls_file = sys.argv[1]

    with open(urls_file, 'r') as file:
        urls = file.read().splitlines()

    for url in urls:
        fetch_url(url)

if __name__ == "__main__":
    main()
