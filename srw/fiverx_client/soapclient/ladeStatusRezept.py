"""
Fragt den Status von zuvor eingelieferten Rezepten ab.

Usage:
    ladeStatusRezept lieferung <LIEFERID> [<STATUS>]
    ladeStatusRezept erezept <EREZEPTID>
    ladeStatusRezept muster16 <MUSTER16ID>
    ladeStatusRezept prezept <TRANSAKTIONSNUMMER> <JAHR>
"""

from .baseutils import assemble_soap_xml, sendHeader_xml
from ..utils import EREZEPT, MUSTER16, PREZEPT


__all__ = [
    'build_soap_xml'
]

def build_soap_xml(header_params, command_args, minimized=False, *, version):
    per_submission_id = bool(command_args['lieferung'])
    query_muster16 = bool(command_args['muster16'])
    query_erezept = bool(command_args['erezept'])
    query_prezept = bool(command_args['prezept'])
    if per_submission_id:
        submission_id = command_args['<LIEFERID>']
        query_xml = query_perLieferID(submission_id, 'ALLE')
    elif query_erezept:
        erezept_id = command_args['<EREZEPTID>']
        query_xml = query_perRezeptID(EREZEPT, erezept_id)
    elif query_muster16:
        muster16_id = command_args['<MUSTER16ID>']
        query_xml = query_perRezeptID(MUSTER16, muster16_id)
    elif query_prezept:
        tid = command_args['<TRANSAKTIONSNUMMER>']
        year = command_args['<JAHR>']
        query_xml = query_perRezeptID(PREZEPT, tid, year)
    template = payload_template.strip()
    sendHeader = sendHeader_xml(**header_params)
    payload_xml = template % {'sendHeader': sendHeader, 'query_xml': query_xml}
    soap_xml = assemble_soap_xml(soap_template, payload_xml, minimized=minimized, version=version)
    return soap_xml

response_payload_xpath = '//fiverx:ladeStatusRezeptResponse/result'

def query_perLieferID(submission_id, status):
    return u'''
        <perLieferID>
            <rzLieferId>%s</rzLieferId>
            <rezeptStatus>%s</rezeptStatus>
        </perLieferID>''' % (submission_id, status)

def query_perRezeptID(ptype, document_id, year=None):
    if ptype == PREZEPT:
        parameter_xml = '''
                <transaktionsNummer>%s</transaktionsNummer>
                <erstellungsJahr>%s</erstellungsJahr>
        ''' % (document_id, year)
    elif ptype == EREZEPT:
        parameter_xml = f'<eRezeptId>{document_id}</eRezeptId>'
    else:
        parameter_xml = '<muster16Id>%s</muster16Id>' % document_id
    return '<perRezeptID>%s</perRezeptID>' % parameter_xml


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

