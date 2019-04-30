
from lxml import etree


__all__ = ['pprint_xml', 'prettify_xml']

def prettify_xml(xml):
    xml_str = xml if isinstance(xml, str) else etree.fromstring(xml)
    # lxml FAQ: "Why doesn't the pretty_print option reformat my XML output?"
    # https://lxml.de/FAQ.html#why-doesn-t-the-pretty-print-option-reformat-my-xml-output
    parser = etree.XMLParser(remove_blank_text=True)
    xml_doc = etree.fromstring(xml_str, parser)
    indented_xml = etree.tostring(xml_doc, pretty_print=True, encoding='unicode')
    return indented_xml

def pprint_xml(xml_str):
    print(prettify_xml(xml_str))

