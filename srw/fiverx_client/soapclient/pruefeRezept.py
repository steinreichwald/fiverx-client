"""
Übermittelt Rezeptdaten zur Prüfung an das RZ.

Usage:
    pruefeRezept [--async] <XML>
"""

from .baseutils import assemble_soap_xml, sendHeader_xml

__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    xml_path = command_args['<XML>']
    async_check = command_args['--async']

    with open(xml_path, 'rb') as xml_fp:
        prescription_xml = xml_fp.read().decode('utf8')
    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_params = {
        'avsId': '12',
        'pruefModus': 'SYNCHRON' if (not async_check) else 'ASYNCHRON',
        'sendHeader': sendHeader,
        'prescription_xml': prescription_xml,
    }
    payload_xml = template % payload_params
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized, version=version)
    return soap_xml

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
