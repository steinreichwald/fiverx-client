
import re

from docopt import docopt
from lxml import etree
from soapfish.lib.attribute_dict import AttrDict


__all__ = [
    'EREZEPT',
    'MUSTER16',
    'decode_xml_bytes',
    'parse_command_args',
    'pprint_xml',
    'prettify_xml',
    'PREZEPT',
    'strip_xml_encoding',
    'textcolor',
]

PREZEPT = 'prezept'
MUSTER16 = 'muster16'
EREZEPT = 'erezept'


def parse_command_args(doc_str, command_args, global_args):
    cmd_args = docopt(doc_str, argv=command_args)
    args = {}
    args.update(global_args)
    args.update(cmd_args)
    return args

def prettify_xml(xml):
    if not isinstance(xml, str):
        xml = etree.tostring(xml)
    xml_str = strip_xml_encoding(xml)
    # lxml FAQ: "Why doesn't the pretty_print option reformat my XML output?"
    # https://lxml.de/FAQ.html#why-doesn-t-the-pretty-print-option-reformat-my-xml-output
    parser = etree.XMLParser(remove_blank_text=True)
    xml_doc = etree.fromstring(xml_str, parser)
    indented_xml = etree.tostring(xml_doc, pretty_print=True, encoding='unicode')
    return indented_xml

def pprint_xml(xml_str):
    print(prettify_xml(xml_str))

def decode_xml_bytes(xml_bytes):
    xml_decl_pattern = b'^<\?xml [^>]*?encoding="([^"]+)".*?>\s*'
    regex_xml_declaration = re.compile(xml_decl_pattern)
    match_decl = regex_xml_declaration.search(xml_bytes)
    if match_decl:
        encoding = match_decl.group(1).decode('ascii')
        xml_str = xml_bytes.decode(encoding)
    else:
        xml_str = xml_bytes.decode('utf8')
    return xml_str

def strip_xml_encoding(xml_str):
    # lxml will complain when loading a ("unicode") string with XML encoding declaration
    if xml_str.startswith('<?xml version='):
        return re.sub('^.+?\?>\s*', '', xml_str)
    return xml_str


# --- colorama utilities -----------------------------------------------------
from contextlib import contextmanager
import sys

try:
    import colorama
    is_colorama_available = True
    TermColor = colorama
except ImportError:
    colorama = None
    is_colorama_available = False
    class TermColor:
        Fore = AttrDict({'GREEN': None, 'RED': None, 'YELLOW': None})
        Style = AttrDict({'BRIGHT': None})

def is_colorama_initialized():
    if not is_colorama_available:
        return False
    return (colorama.initialise.orig_stdout is not None)

@contextmanager
def textcolor(color):
    if not is_colorama_available:
        yield
        return
    if not is_colorama_initialized():
        colorama.init()
    sys.stdout.write(color)
    yield
    sys.stdout.write(colorama.Style.RESET_ALL)
