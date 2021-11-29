"""
Setzt den Status eines zuvor eingelieferten Rezepts auf "storniert".

Usage:
    storniereRezept muster16 <MUSTER16ID>
    storniereRezept prezept <TRANSAKTIONSNUMMER> <JAHR>
"""

from .baseutils import assemble_soap_xml, sendHeader_xml


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    cancel_muster16 = bool(command_args['muster16'])
    cancel_prezept = bool(command_args['prezept'])
    if cancel_muster16:
        muster16_id = command_args['<MUSTER16ID>']
        query_xml = '<muster16Id>%s</muster16Id>' % muster16_id
    elif cancel_prezept:
        tid = command_args['<TRANSAKTIONSNUMMER>']
        year = command_args['<JAHR>']
        query_xml = '''
            <transaktionsNummer>%s</transaktionsNummer>
            <erstellungsJahr>%s</erstellungsJahr>
            ''' % (tid, year)
    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_xml = template % {'sendHeader': sendHeader, 'query_xml': query_xml}
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized, version=version)
    return soap_xml

response_payload_xpath = '//fiverx:storniereRezeptResponse/result'

payload_template = '''
<?xml version='1.0' encoding='UTF-8'?>
<rzeParamStorno xmlns="http://fiverx.de/spec/abrechnungsservice">
  %(sendHeader)s
  %(query_xml)s
</rzeParamStorno>
'''

soap_template = '''
<senv:Envelope xmlns:senv="http://schemas.xmlsoap.org/soap/envelope/">
<senv:Body>
<fiverx:storniereRezept xmlns:fiverx="http://fiverx.de/spec/abrechnungsservice/types">
    <rzeParamStorno>%(payload)s</rzeParamStorno>
    <rzeParamVersion>%(rze_param_version)s</rzeParamVersion>
</fiverx:storniereRezept>
</senv:Body></senv:Envelope>
'''

