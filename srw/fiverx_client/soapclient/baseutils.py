
import sys

from lxml import etree
import requests

from ..utils import strip_xml_encoding


__all__ = [
    'assemble_soap_xml',
    'extract_response_payload',
    'minimize_xml',
    'sendHeader_xml',
    'send_request',
]

sendHeader_template = '''
<sendHeader>
    <rzKdNr>%(user)s</rzKdNr>
    <avsSw>
        <hrst>SRW</hrst>
        <nm>Testclient</nm>
        <vs>1.0</vs>
    </avsSw>
    <apoIk>%(apoik)s</apoIk>
    <test>%(test)s</test>
    <pw>%(password)s</pw>
</sendHeader>
'''

def sendHeader_xml(**kwargs):
    return sendHeader_template % kwargs

rzeParamVersion_xml = '''
<?xml version="1.0" encoding="ISO-8859-15"?>
<rzeParamVersion xmlns="http://fiverx.de/spec/abrechnungsservice">
    <versionNr>01.08</versionNr>
</rzeParamVersion>
'''.strip()

def _escape_xml(xml):
    return xml.replace('<', '&lt;').replace('>', '&gt;')

def assemble_soap_xml(soap_template, payload_xml, minimized=False):
    if minimized:
        payload_xml = minimize_xml(payload_xml)
    payload_str = _escape_xml(payload_xml)
    version_str = _escape_xml(rzeParamVersion_xml)
    soap_xml = soap_template.strip() % {'payload': payload_str, 'rze_param_version': version_str}

    # validate XML
    try:
        soap_bytes = soap_xml.encode('utf8')
        etree.fromstring(soap_bytes)
    except etree.XMLSyntaxError as e:
        print('==> invalid request XML: %s <==' % e)
        print(soap_xml)
        sys.exit(20)
    return soap_xml

def send_request(ws_url, soap_xml, chunked=True):
    charset_str = 'UTF-8'
    def payload_gen():
        # requests 2.8.1 raised an exception when I passed str data for a
        # chunked request and required byte data
        # We set the charset anyway in the Content-Type header so we can also
        # encode the request data here.
        yield soap_xml.encode(charset_str)
    headers = {
        'SOAPAction': '',
        'User-Agent': 'Python SRW Testclient',
        'Content-Type': 'text/xml; charset=' + charset_str,
    }
    if chunked:
        headers['Transfer-Encoding'] = 'chunked'
        data = payload_gen()
    else:
        data = soap_xml
    response = requests.post(ws_url, data=data, headers=headers)
    return response

def minimize_xml(xml_str):
    minimized_payload = ''
    for i, line in enumerate(xml_str.split('\n')):
        minimized_payload += line.strip()
        if i == 0:
            minimized_payload += '\n'
    return minimized_payload

def extract_response_payload(root, xpath):
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'fiverx': 'http://fiverx.de/spec/abrechnungsservice/types',
    }
    matched_elements = root.xpath(xpath, namespaces=namespaces)
    if matched_elements:
        payload_str = matched_elements[0].text
    else:
        payload_str = root.text
    if payload_str:
        payload_str = strip_xml_encoding(payload_str)
    return payload_str
