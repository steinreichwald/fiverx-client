"""
Sendet den Inhalt der <XML>-Datei als SOAP-Anfrage ohne weitere Formatierung.

Dieser Modus kann zum Replay echter Requests verwendet werden.

Usage:
    raw <XML>
"""


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    xml_path = command_args['<XML>']
    with open(xml_path, 'rb') as xml_fp:
        soap_xml = xml_fp.read().decode('utf8')
    return soap_xml

response_payload_xpath = '//fiverx:*/result'

