"""
Übermittelt Rezeptdaten zur Prüfung an das RZ.

Usage:
    pruefeRezept [--async] <XML>
"""

from lxml import etree

from .baseutils import assemble_soap_xml, sendHeader_xml
from .payload_helpers import is_eDispensierung, wrap_eDispensierung_in_fiverx_erezept
from ..utils import decode_xml_bytes, strip_xml_encoding


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    xml_path = command_args['<XML>']
    async_check = command_args['--async']

    with open(xml_path, 'rb') as xml_fp:
        prescription_bytes = xml_fp.read()

    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_params = {
        'avsId': '12',
        'pruefModus': 'SYNCHRON' if (not async_check) else 'ASYNCHRON',
        'sendHeader': sendHeader,
        'prescription_xml': prescription_data_as_xml(prescription_bytes),
    }
    payload_xml = template % payload_params
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized, version=version)
    return soap_xml

def prescription_data_as_xml(data):
    xml_str = strip_xml_encoding(decode_xml_bytes(data))
    xml_doc = etree.fromstring(xml_str)
    if not is_eDispensierung(xml_doc):
        return xml_str
    return wrap_eDispensierung_in_fiverx_erezept(xml_doc, data)

response_payload_xpath = '//fiverx:pruefeRezeptResponse/result'

payload_template = '''
<?xml version='1.0' encoding='UTF-8'?>
<rzePruefung xmlns="http://fiverx.de/spec/abrechnungsservice">
  %(sendHeader)s
  <rzPruefungBody>
    <avsId>%(avsId)s</avsId>
    <pruefModus>%(pruefModus)s</pruefModus>
    %(prescription_xml)s
  </rzPruefungBody>
</rzePruefung>
'''

soap_template = '''
<senv:Envelope xmlns:senv="http://schemas.xmlsoap.org/soap/envelope/">
<senv:Body>
<fiverx:pruefeRezept xmlns:fiverx="http://fiverx.de/spec/abrechnungsservice/types">
    <rzePruefung>%(payload)s</rzePruefung>
    <rzeParamVersion>%(rze_param_version)s</rzeParamVersion>
</fiverx:pruefeRezept>
</senv:Body></senv:Envelope>
'''
