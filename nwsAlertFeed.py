import time
import requests
import xml.etree.ElementTree as ET
import threading
import win32timezone
import datetime as DT
import random

NS = {'atom': "http://www.w3.org/2005/Atom",
      'cap' : "urn:oasis:names:tc:emergency:cap:1.1"}

def expireThread(*args, **kwargs):
    return _expireThread(*args, **kwargs)

class _expireThread(threading.Thread):
    def __init__(self, interval, target, args=[], kwargs={}):
        threading.Thread.__init__(self, group=None, target=target, args=args, kwargs=kwargs)
        self.interval = interval
        #self.target = target
        #self.args = args
        #self.kwargs = kwargs
        self.finished = threading.Event()
        #print self._Thread__stopped

    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()

    def run(self):
        self.finished.wait(self.interval)
        try:
            if not self.finished.is_set():
                self._Thread__target(*self._Thread__args, **self._Thread__kwargs)
            self.finished.set()
        finally:
            self._Thread__stopped = True
            del self._Thread__target, self._Thread__args, self._Thread__kwargs

    def dummy_function(*args, **kwargs):
        pass

def tz_now():
    return DT.datetime.utcnow().replace(tzinfo=win32timezone.TimeZoneInfo('UTC'))

def tz_parse(dt_string):
    parsed = DT.datetime.strptime(dt_string[:-6], '%Y-%m-%dT%H:%M:%S')
    timezone = dt_string[-6:]
    tzoffset = DT.timedelta(hours=int(timezone[:-3]))
    parsed = parsed - tzoffset
    parsed = parsed.replace(tzinfo=win32timezone.TimeZoneInfo("UTC"))

    return parsed

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
            break #There are no events
        entryURL = entry.find("atom:id", namespaces=NS).text
        entryID = entryURL.split('?x=', 1)[1].split('.')[4]
        if entryURL in alert_keys:
            del alert_keys[entryURL]
        entryUpdated = entry.find('atom:updated', namespaces=NS).text
        entryExpires = entry.find('cap:expires', namespaces=NS).text
        dtExpires = tz_parse(entry.find('cap:expires', namespaces=NS).text)
        now = tz_now()
        secExpires = (dtExpires - now).total_seconds()
        #print dtExpires.astimezone(win32timezone.TimeZoneInfo('Central Standard Time'))
        if alerts.get(entryURL, {'entryUpdated':""})['entryUpdated'] != entryUpdated and \
            secExpires > 0.0 :
            print alerts.get(entryURL, {'entryUpdated':""})['entryUpdated']
            print entryUpdated
            t = expireThread(float(secExpires + random.randint(0,10)),
                                removeAlert, args=(alerts, entryURL), kwargs={})
            t.daemon = True
            t.start()
            if entryURL in alerts:
                print "Updating alert"
                old_t = alerts[entryURL]['thread']
                #print old_t
                old_t.cancel()
                #print "Is it still alive? ", old_t.isAlive()
            else:
                print "New Alert"
                alerts[entryURL] = {'entryUpdated':entryUpdated, 'entryExpires':entryExpires,
                                   'thread':t}
            print "Expiring this alert in {0} seconds".format(secExpires)
            print entry.find('atom:title', namespaces=NS).text
            print entryURL
            print "Updated", entryUpdated
            print "Effective", entry.find('cap:effective', namespaces=NS).text
            print "Expires", entryExpires

    print "Number of entries", len(feed.findall('atom:entry', namespaces=NS))
    print "Left over keys", alert_keys
    for key in alert_keys:
        print "Dropping the alert", key
        t = alerts[key]['thread']
        t.cancel()
        #print t
        #time.sleep(2)
        #print "Is it alive? ", t.isAlive()
        del alerts[key]

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
        print "Number of timers", len(filter(lambda t: type(t)== _expireThread, threading.enumerate()))
        #print threading.enumerate()
        #print threading.activeCount()
        print "Number of active alerts: ", len(alerts.keys())
        time.sleep(30.0)
        lastupdated = checkFeed('http://alerts.weather.gov/cap/us.atom', alerts, lastupdated )
        time.sleep(15.0)
        #print "lastupdated", lastupdated


if __name__ == '__main__':
    main()
