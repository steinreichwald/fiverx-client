
import sys

from lxml import etree
import requests
try:
    from requests.packages import urllib3
except ImportError:
    import urllib3

from ..utils import strip_xml_encoding


__all__ = [
    'assemble_soap_xml',
    'extract_response_payload',
    'match_xpath',
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
    <versionNr>%(version)s</versionNr>
</rzeParamVersion>
'''.strip()

def _escape_xml(xml):
    return xml.replace('<', '&lt;').replace('>', '&gt;')

def assemble_soap_xml(soap_template, payload_xml, minimized=False, *, version='01.08'):
    if minimized:
        payload_xml = minimize_xml(payload_xml)
    payload_str = _escape_xml(payload_xml)
    version_str = _escape_xml(rzeParamVersion_xml % {'version': version})
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

def send_request(ws_url, soap_xml, chunked=True, *, verify_cert=True, hostname=None):
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
    if hostname:
        headers['Host'] = hostname
    if chunked:
        headers['Transfer-Encoding'] = 'chunked'
        data = payload_gen()
    else:
        data = soap_xml
    if not verify_cert:
        # avoid "InsecureRequestWarning" from urllib3:
        # "Unverified HTTPS request is being made. Adding certificate verification is strongly advised."
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.post(ws_url, data=data, headers=headers, verify=verify_cert, allow_redirects=False)
    return response

def minimize_xml(xml_str):
    minimized_payload = ''
    for i, line in enumerate(xml_str.split('\n')):
        minimized_payload += line.strip()
        if i == 0:
            minimized_payload += '\n'
    return minimized_payload

def match_xpath(root, xpath):
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'fiverx': 'http://fiverx.de/spec/abrechnungsservice/types',
    }
    matched_elements = root.xpath(xpath, namespaces=namespaces)
    if matched_elements:
        return matched_elements[0]
    return None

def extract_response_payload(root, xpath):
    element = match_xpath(root, xpath)
    if element is not None:
        payload_str = element.text.strip()
    else:
        return ''
    return strip_xml_encoding(payload_str)
