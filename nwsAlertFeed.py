import time
import requests
import xml.etree.ElementTree as ET
import threading
import win32timezone
import datetime as DT
import random

NS = {'atom': "http://www.w3.org/2005/Atom",
      'cap' : "urn:oasis:names:tc:emergency:cap:1.1"}

def processFeed(r, alerts, lastupdated):
    print "HTTP Expires", r.headers['expires']

    alert_keys = {}.fromkeys(alerts.iterkeys(), None)
    #print alert_keys
    feed = ET.fromstring(r.content)
    updated = feed.find('atom:updated', namespaces=NS).text
    if updated != lastupdated:
        print "Feed updated", updated
    for entry in feed.findall('atom:entry', namespaces=NS):
        if entry.find("atom:link", namespaces=NS).attrib['href'] == r.url:
            break
        entryID = entry.find("atom:id", namespaces=NS).text
        if entryID in alert_keys:
            del alert_keys[entryID]
        entryUpdated = entry.find('atom:updated', namespaces=NS).text
        entryExpires = entry.find('cap:expires', namespaces=NS).text
        timezone = entryExpires[-6:]
        #print entryExpires, timezone[:-3]
        dtExpires = DT.datetime.strptime(entryExpires[:-6], '%Y-%m-%dT%H:%M:%S')
        tzoffset = DT.timedelta(hours=int(timezone[:-3]))
        dtExpires = dtExpires - tzoffset
        dtExpires = dtExpires.replace(tzinfo=win32timezone.TimeZoneInfo("UTC"))
        now = DT.datetime.utcnow().replace(tzinfo=win32timezone.TimeZoneInfo('UTC'))
        secExpires = (dtExpires - now).total_seconds()
        #print dtExpires.astimezone(win32timezone.TimeZoneInfo('Central Standard Time'))
        if alerts.get(entryID, {'entryUpdated':""})['entryUpdated'] != entryUpdated and \
            secExpires > 0.0 :
            t = threading.Timer(float(secExpires),
                                removeAlert, args=(alerts, entryID), kwargs={})
            t.daemon = True
            t.start()
            alerts[entryID] = {'entryUpdated':entryUpdated, 'entryExpires':entryExpires,
                               'thread':t}
            print "New alert"
            print "Expiring this alert in {0} seconds".format(secExpires)
            print entry.find('atom:title', namespaces=NS).text
            print entryID
            print "Updated", entryUpdated
            print "Effective", entry.find('cap:effective', namespaces=NS).text
            print "Expires", entryExpires

    print "Left over keys", alert_keys
    return updated

def checkFeed(url, alerts, lastupdated):
    try:
        lastupdated = processFeed(requests.get(url), alerts, lastupdated)
    except Exception as e:
        print "An exception occurred", e
        return ""
    else:
        return lastupdated

def removeAlert(alerts, key):
    print "I removed the alert", key
    del alerts[key]

def main():

    alerts = {}
    lastupdated = ''

    while True:
        lastupdated = checkFeed('http://alerts.weather.gov/cap/us.atom', alerts, lastupdated )
        print "Number of timers", len(filter(lambda t: type(t)== threading._Timer, threading.enumerate()))
        print "Number of active alerts: ", len(alerts.keys())
        time.sleep(30.0)
        #print "lastupdated", lastupdated


if __name__ == '__main__':
    main()
