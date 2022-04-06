"""
Übermittelt Rezeptdaten an das RZ.

Die XML-Dateien können eMuster16-, eRezept- oder pRezept-Daten enthalten und
werden dann in eine entsprechende <rzeLeistung>-Struktur eingebunden.

Falls nur eine XML-Datei angegeben wurde und diese bereits die komplette
<rzeLeistung>-Struktur enthält, wird nur der SOAP-Body zusätzlich generiert
(Zugangsdaten aus der ini-Datei bleiben in diesem Fall unberücksichtigt).

Usage:
    sendeRezepte <XML>...
"""

from base64 import b64encode
from pathlib import Path
import sys

from lxml import etree
from lxml.etree import XMLSyntaxError

from .baseutils import assemble_soap_xml, sendHeader_xml
from ..utils import decode_xml_bytes, strip_xml_encoding, textcolor, TermColor


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    xml_paths = command_args['<XML>']

    xml_contents = []
    for xml_path in xml_paths:
        source_path = Path(xml_path)
        with source_path.open('rb') as xml_fp:
            xml_bytes = xml_fp.read()
        xml_contents.append(xml_bytes)

    if not is_payload_xml(xml_contents):
        rzLeistungInhalte = []
        for xml_bytes in xml_contents:
            body_str = _eleistung_body(xml_bytes, source_path, version=version)
            leistung_params = dict(avsId='12345', prescription_xml=body_str)
            rzLeistungInhalt = rzLeistungInhalt_template % leistung_params
            rzLeistungInhalte.append(rzLeistungInhalt)
        template = payload_template.strip()
        sendHeader = sendHeader_xml(**header_params)
        payload_params = {
            'sendHeader': sendHeader,
            'rzLeistungInhalte_xml': '\n'.join(rzLeistungInhalte),
        }
        payload_xml = template % payload_params
    else:
        payload_xml = decode_xml_bytes(xml_contents[0])
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized, version=version)
    return soap_xml

def is_payload_xml(xml_contents):
    if len(xml_contents) != 1:
        return False
    xml_bytes = xml_contents[0]
    xml_str = strip_xml_encoding(decode_xml_bytes(xml_bytes))
    xml_doc = etree.fromstring(xml_str)
    tag_name = xml_doc.tag
    return (tag_name == '{http://fiverx.de/spec/abrechnungsservice}rzeLeistung')

def _eleistung_body(xml_bytes, source_path, *, version):
    xml_str = strip_xml_encoding(decode_xml_bytes(xml_bytes))
    try:
        xml_doc = etree.fromstring(xml_str)
    except XMLSyntaxError as e:
        with textcolor(TermColor.Fore.RED):
            print(f'{source_path.name}: invalid XML for eLeistungBody {e.msg}')
        sys.exit(1)

    is_erezept = (xml_doc.tag == 'eDispensierung')
    if not is_erezept:
        return xml_str
    if version != '01.10':
        with textcolor(TermColor.Fore.RED):
            print(f'{source_path.name}: eRezepte können nur über API-Version 1.10 verschickt werden')
        sys.exit(1)
    erezept_id = xml_doc.attrib['RezeptId']
    b64_edispensierung = b64encode(xml_bytes.strip()).decode('ASCII')
    return erezept_template % {'id': erezept_id, 'data': b64_edispensierung}

response_payload_xpath = '//fiverx:sendeRezepteResponse/result'

erezept_template = '''
  <eRezept>
    <eRezeptId>%(id)s</eRezeptId>
    <eRezeptData>%(data)s</eRezeptData>
  </eRezept>
'''

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

