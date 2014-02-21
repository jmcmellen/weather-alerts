import time
import requests


def processFeed(r, *args, **kwargs):
    print r.headers
    for item in args:
        print item
    for key in kwargs:
        print key + " ==> " + kwargs[key]

def checkFeed(url):
    requests.get(url, hooks=dict(response=processFeed))

def main():

    while True:
        checkFeed('http://alerts.weather.gov/cap/mo.php?x=0')
        time.sleep(300)

if __name__ == '__main__':
    main()
