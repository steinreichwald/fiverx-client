
from lxml import etree, objectify
from lxml.etree import XMLSchema
import pkg_resources

from ..lib import Result

__all__ = ['validate_payload']


def validate_payload(payload_string):
    parent_module = __name__.rsplit('.', 1)[0]
    xsd_string = pkg_resources.resource_string(parent_module+'.static', 'RZeRezept_01_08.xsd')
    xmlschema = XMLSchema(etree.fromstring(xsd_string))
    parser = objectify.makeparser(schema=xmlschema)

    if isinstance(payload_string, str):
        payload_string = payload_string.encode('utf-8')
    try:
        validated_document = objectify.fromstring(payload_string.strip(), parser=parser)
    except etree.XMLSyntaxError as e:
        return Result(False, errors=[e])
    return Result(True, validated_document=validated_document, errors=None)

