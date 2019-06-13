"""
Fragt den Status von zuvor eingelieferten Rezepten ab.

Usage:
    ladeStatusRezept lieferung <LIEFERID> [<STATUS>]
"""

from .baseutils import assemble_soap_xml, sendHeader_xml


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False):
    per_submission_id = bool(command_args['lieferung'])
    if per_submission_id:
        submission_id = command_args['<LIEFERID>']
        query_xml = query_perLieferID(submission_id, 'ALLE')
    else:
        raise NotImplementedError('on perLieferung is implemented right now')
    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_xml = template % {'sendHeader': sendHeader, 'query_xml': query_xml}
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized)
    return soap_xml

response_payload_xpath = '//fiverx:ladeStatusRezeptResponse/result'

def query_perLieferID(submission_id, status):
    return u'''
        <perLieferID>
            <rzLieferId>%s</rzLieferId>
            <rezeptStatus>%s</rezeptStatus>
        </perLieferID>''' % (submission_id, status)


payload_template = '''
<?xml version='1.0' encoding='UTF-8'?>
<rzeParamStatus xmlns="http://fiverx.de/spec/abrechnungsservice">
  %(sendHeader)s
  %(query_xml)s
</rzeParamStatus>
'''

soap_template = '''
<senv:Envelope xmlns:senv="http://schemas.xmlsoap.org/soap/envelope/">
<senv:Body>
<fiverx:ladeStatusRezept xmlns:fiverx="http://fiverx.de/spec/abrechnungsservice/types">
    <rzeParamStatus>%(payload)s</rzeParamStatus>
    <rzeParamVersion>%(rze_param_version)s</rzeParamVersion>
</fiverx:ladeStatusRezept>
</senv:Body></senv:Envelope>
'''

