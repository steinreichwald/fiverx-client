#!/usr/bin/env python

from __future__ import division, absolute_import, print_function, unicode_literals

from argparse import ArgumentParser
try:
    from configparser import SafeConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser
from datetime import datetime as DateTime
import os
import time

from babel.util import LOCALTZ
from soapfish import xsd
import requests
from requests.auth import HTTPBasicAuth


def submission_xml(prescription_xml):
    xml = '''<?xml version="1.0" encoding="utf-8"?>
<rzeLeistung xmlns="http://fiverx.de/spec/abrechnungsservice">
    <rzLeistungHeader>
        <sendHeader>
            <rzKdNr>....</rzKdNr>
            <avsSw>
                <hrst>SRW</hrst>
                <nm>Python SOAP Fetch Client</nm>
                <vs>1</vs>
            </avsSw>
            <apoIk>000000000</apoIk>
            <pw>000000</pw>
        </sendHeader>
        <sndId>00000</sndId>
    </rzLeistungHeader>
    <rzLeistungInhalt>
        <eLeistungHeader>
            <avsId>00000</avsId>
        </eLeistungHeader>
        <eLeistungBody>
            %s
        </eLeistungBody>
    </rzLeistungInhalt>
</rzeLeistung>''' % prescription_xml
    return xml

def store_prescription(prescription_data, result_dir):
    id_ = prescription_data['id']
    pharmacy_id = prescription_data['pharmacy_id']
    now = time.time()
    content_xml = prescription_data['content_xml']
    
    filename = '%(id)06d-%(pharmacy_id)s-%(time)s.xml' % (dict(id=id_, pharmacy_id=pharmacy_id, time=now))
    path = os.path.join(result_dir, filename)
    with open(path, 'wb') as fp:
        binary_xml = submission_xml(content_xml).encode('utf8')
        fp.write(binary_xml)


def fetch(export_dir, settings, since=None):
    base_url = settings['url']
    user = settings['username']
    password = settings['password']
    
    path = '/internal/export-prescriptions/'
    url = base_url + path
    if since:
        url += xsd.DateTime().xmlvalue(since)
    
    response = requests.post(url, auth=HTTPBasicAuth(user, password))
    if response.status_code != 200:
        print('Error while fetching data: %r (code: %r)' % (response.text, response.status_code))
        return
    results = response.json()
    
    now = DateTime.now(LOCALTZ)
    # Windows does not like ':' in path names
    pathname = xsd.DateTime().xmlvalue(now).replace(':', '_')
    result_dir = os.path.join(export_dir, pathname)
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    for prescription_data in results['prescriptions']:
        store_prescription(prescription_data, result_dir)


def main():
    parser = ArgumentParser(description='export prescription data from srw.link service.')
    parser.add_argument('--config', dest='config_filename', default='fiverx.ini')
    parser.add_argument('--since', dest='since')
    parser.add_argument('export_dir')
    
    args = parser.parse_args()
    
    config = SafeConfigParser()
    config.read(args.config_filename)
    settings = dict(config.items('srw.link'))
    
    since = None
    if args.since:
        since = xsd.DateTime().pythonvalue(args.since)
    
    fetch(args.export_dir, settings, since)

if __name__ == '__main__':
    main()
