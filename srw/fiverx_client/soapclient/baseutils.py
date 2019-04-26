
import sys

from lxml import etree
import requests


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
    <pw>%(password)s</pw>
</sendHeader>
'''

def sendHeader_xml(**kwargs):
    return sendHeader_template % kwargs


def assemble_soap_xml(soap_template, payload_xml, minimized=False):
    if minimized:
        payload_xml = minimize_xml(payload_xml)
    payload_str = payload_xml.replace('<', '&lt;').replace('>', '&gt;')
    soap_xml = soap_template.strip() % {'payload': payload_str}

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
    def payload_gen():
        yield soap_xml
    headers = {
        'SOAPAction': '',
        'User-Agent': 'Python SRW Testclient',
        'Content-Type': 'text/xml; charset=UTF-8',
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
    payload_str = matched_elements[0].text
    return payload_str
