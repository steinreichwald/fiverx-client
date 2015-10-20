#!/usr/bin/env python

from __future__ import division, absolute_import, print_function, unicode_literals

from argparse import ArgumentParser
from ConfigParser import SafeConfigParser
from datetime import datetime as DateTime
import os
import time

from babel.util import LOCALTZ
from soapfish import xsd
import requests
from requests.auth import HTTPBasicAuth


def submission_xml(customer_id, pharmacy_id, password, prescription_xml_template):
    prescription_xml = prescription_xml_template % dict(pharmacy_id=pharmacy_id)
    parameters = dict(
        customer_id=customer_id,
        pharmacy_id=pharmacy_id,
        password=password,
        prescription_xml=prescription_xml,
    )
    xml = '''<?xml version="1.0" encoding="utf-8"?>
<rzeLeistung xmlns="http://fiverx.de/spec/abrechnungsservice">
    <rzLeistungHeader>
        <sendHeader>
            <rzKdNr>%(customer_id)s</rzKdNr>
            <avsSw>
                <hrst>SRW</hrst>
                <nm>Python SOAP Dummy Submission Client</nm>
                <vs>1</vs>
            </avsSw>
            <apoIk>%(pharmacy_id)s</apoIk>
            <pw>%(password)s</pw>
        </sendHeader>
        <sndId>00000</sndId>
    </rzLeistungHeader>
    <rzLeistungInhalt>
        <eLeistungHeader>
            <avsId>00000</avsId>
        </eLeistungHeader>
        <eLeistungBody>
            %(prescription_xml)s
        </eLeistungBody>
    </rzLeistungInhalt>
</rzeLeistung>''' % parameters
    return xml


def soap_message(payload_xml):
    payload_string = payload_xml.replace('<', '&lt;').replace('>', '&gt;')
    
    soap_envelope_template = u'''<?xml version='1.0' encoding='UTF-8'?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
    <soapenv:Body>
    <ns1:sendeRezepte xmlns:ns1="http://fiverx.de/spec/abrechnungsservice/types">
        <rzeLeistung>%(payload_string)s</rzeLeistung>
        <rzeParamVersion>&lt;?xml version="1.0" encoding="utf-8"?&gt;
&lt;rzeParamVersion xmlns="http://fiverx.de/spec/abrechnungsservice"&gt;
            &lt;versionNr&gt;01.08&lt;/versionNr&gt;
        &lt;/rzeParamVersion&gt;</rzeParamVersion>
    </ns1:sendeRezepte>
    </soapenv:Body></soapenv:Envelope>'''
    return soap_envelope_template % dict(payload_string=payload_string)


def submit(settings, prescription_template):
    base_url = settings['url']
    user = settings['username']
    password = settings['password']
    pharmacy_id = settings['pharmacy_id']
    
    url = base_url + '/'
    
    prescription_xml = submission_xml(user, pharmacy_id, password, prescription_template)
    xml = soap_message(prescription_xml)
    
    response = requests.post(url, data=xml)
    if response.status_code != 200:
        print('Error while fetching data: %r (code: %r)' % (response.text, response.status_code))
        return
    print(response.text)


def main():
    parser = ArgumentParser(description='submit dummy prescription data to the srw.link service.')
    parser.add_argument('--config', dest='config_filename', default='submission.ini')
    parser.add_argument('prescription_filename')
    
    args = parser.parse_args()
    
    config = SafeConfigParser()
    config.read(args.config_filename)
    settings = dict(config.items('srw.link'))
    
    prescription_xml = open(args.prescription_filename).read()
    submit(settings, prescription_xml)

if __name__ == '__main__':
    main()
