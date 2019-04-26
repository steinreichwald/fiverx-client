
from .baseutils import assemble_soap_xml, sendHeader_xml


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, minimized=False):
    template = payload_template.lstrip('\n')
    sendHeader = sendHeader_xml(**header_params)
    payload_xml = template % {'sendHeader': sendHeader}
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized)
    return soap_xml

response_payload_xpath = '//fiverx:ladeRzVersionResponse/result'

payload_template = '''
<?xml version='1.0' encoding='UTF-8'?>
<rzeParamLadeVersion xmlns="http://fiverx.de/spec/abrechnungsservice">
  %(sendHeader)s
</rzeParamLadeVersion>
'''

soap_template = '''
<senv:Envelope xmlns:senv="http://schemas.xmlsoap.org/soap/envelope/">
<senv:Body>
  <fiverx:ladeRzVersion xmlns:fiverx="http://fiverx.de/spec/abrechnungsservice/types">
    <rzeParamLadeVersion>%(payload)s</rzeParamLadeVersion>
  </fiverx:ladeRzVersion>
</senv:Body></senv:Envelope>
'''
