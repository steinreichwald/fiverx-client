
from base64 import b64encode


__all__ = [
    'is_eDispensierung',
    'wrap_eDispensierung_in_fiverx_erezept',
]

def is_eDispensierung(xml_doc):
    return xml_doc.tag == 'eDispensierung'

def wrap_eDispensierung_in_fiverx_erezept(xml_doc, xml_bytes):
    erezept_id = xml_doc.attrib['RezeptId']
    b64_edispensierung = b64encode(xml_bytes.strip()).decode('ASCII')
    return erezept_template % {'id': erezept_id, 'data': b64_edispensierung}

erezept_template = '''
  <eRezept>
    <eRezeptId>%(id)s</eRezeptId>
    <eRezeptData>%(data)s</eRezeptData>
  </eRezept>
'''
