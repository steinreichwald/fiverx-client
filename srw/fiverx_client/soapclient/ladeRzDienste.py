"""
Lade die vom RZ angebotenen Dienste.

Usage:
    ladeRzDienste
"""

from .baseutils import assemble_soap_xml, sendHeader_xml


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False):
    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_xml = template % {'sendHeader': sendHeader}
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized)
    return soap_xml

response_payload_xpath = '//fiverx:ladeRzDiensteResponse/result'

payload_template = '''
<?xml version='1.0' encoding='UTF-8'?>
<rzeParamDienste xmlns="http://fiverx.de/spec/abrechnungsservice">
  %(sendHeader)s
</rzeParamDienste>
'''

soap_template = '''
<senv:Envelope xmlns:senv="http://schemas.xmlsoap.org/soap/envelope/">
<senv:Body>
<fiverx:ladeRzDienste xmlns:fiverx="http://fiverx.de/spec/abrechnungsservice/types">
    <rzeParamDienste>%(payload)s</rzeParamDienste>
    <rzeParamVersion>%(rze_param_version)s</rzeParamVersion>
</fiverx:ladeRzDienste>
</senv:Body></senv:Envelope>
'''

