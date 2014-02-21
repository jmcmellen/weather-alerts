import time
import requests
import xml.etree.ElementTree as ET
import win32timezone
from urllib import quote
from urlparse import parse_qsl

NS = {'atom': "http://www.w3.org/2005/Atom",
      'cap' : "urn:oasis:names:tc:emergency:cap:1.1"}

def processFeed(r, alerts):
    print r.headers

    feed = ET.fromstring(r.content)
    print "Updated on", feed.find('atom:updated', namespaces=NS).text
    for entry in feed.findall('atom:entry', namespaces=NS):
        #entryID = parse_qsl(entry.find('atom:id', namespaces=NS).text)[0][1]
        entryID = entry.find("atom:id", namespaces=NS).text
        entryUpdated = entry.find('atom:updated', namespaces=NS).text
        if alerts.get(entryID) != entryUpdated:
            alerts[entryID] = entryUpdated
            print "New alert"
            print entry.find('atom:title', namespaces=NS).text
            print entryID
            print entryUpdated
            print entry.find('atom:updated', namespaces=NS).text
            print "Effective", entry.find('cap:effective', namespaces=NS).text
            print "Expires", entry.find('cap:expires', namespaces=NS).text

def checkFeed(url, alerts):
    processFeed(requests.get(url), alerts)


def main():

    alerts = {}

    while True:
        checkFeed('http://alerts.weather.gov/cap/mo.php?x=0', alerts)
        time.sleep(300)
        print "Number of active alerts: ", len(alerts.keys())

if __name__ == '__main__':
    main()
