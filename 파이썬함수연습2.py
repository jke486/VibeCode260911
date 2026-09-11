#파이썬함수 연습2.py

def connectURL(server, port):
    #f-string은 변수명을 바로넘김
    strUrl = f"http://{server}:{port}"
    return strUrl

print(connectURL("kpc.com", 8080))