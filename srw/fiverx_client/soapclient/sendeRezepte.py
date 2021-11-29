"""
Übermittelt Rezeptdaten an das RZ.

Usage:
    sendeRezepte <XML>...
"""

from .baseutils import assemble_soap_xml, sendHeader_xml
from ..utils import decode_xml_bytes, strip_xml_encoding

__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    xml_paths = command_args['<XML>']

    rzLeistungInhalte = []
    for xml_path in xml_paths:
        with open(xml_path, 'rb') as xml_fp:
            xml_bytes = xml_fp.read()
        xml_str = strip_xml_encoding(decode_xml_bytes(xml_bytes))
        leistung_params = dict(avsId='12345', prescription_xml=xml_str)
        rzLeistungInhalt = rzLeistungInhalt_template % leistung_params
        rzLeistungInhalte.append(rzLeistungInhalt)

    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_params = {
        'sendHeader': sendHeader,
        'rzLeistungInhalte_xml': '\n'.join(rzLeistungInhalte),
    }
    payload_xml = template % payload_params
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized, version=version)
    return soap_xml

response_payload_xpath = '//fiverx:sendeRezepteResponse/result'

rzLeistungInhalt_template = '''
    <rzLeistungInhalt>
        <eLeistungHeader>
            <avsId>%(avsId)s</avsId>
        </eLeistungHeader>
        <eLeistungBody>
            %(prescription_xml)s
        </eLeistungBody>
    </rzLeistungInhalt>
'''

payload_template = '''
<?xml version='1.0' encoding='UTF-8'?>
<rzeLeistung xmlns="http://fiverx.de/spec/abrechnungsservice">
  <rzLeistungHeader>
    %(sendHeader)s
    <sndId>42</sndId>
  </rzLeistungHeader>
  %(rzLeistungInhalte_xml)s
</rzeLeistung>
'''

soap_template = '''
<senv:Envelope xmlns:senv="http://schemas.xmlsoap.org/soap/envelope/">
<senv:Body>
<fiverx:sendeRezepte xmlns:fiverx="http://fiverx.de/spec/abrechnungsservice/types">
    <rzeLeistung>%(payload)s</rzeLeistung>
    <rzeParamVersion>%(rze_param_version)s</rzeParamVersion>
</fiverx:sendeRezepte>
</senv:Body></senv:Envelope>
'''

