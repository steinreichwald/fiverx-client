#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
srwlink-extract-payload

CLI application to extract/validate fiverx XML from recorded SOAP requests.

This can help to answer questions like:
- Why is the sent XML request invalid?
- Show nicely formatted response data to diagnose what happened with some data

Usage:
  srwlink-extract-payload [options] <filename>
"""
import re
import sys

from docopt import docopt
from lxml import etree

from .soapclient import match_xpath, validate_payload
from .utils import is_colorama_available, prettify_xml, textcolor, TermColor


def extract_payload_main(argv=sys.argv):
    arguments = docopt(__doc__, argv=argv[1:])
    input_fn = arguments['<filename>']
    with open(input_fn, 'rb') as input_fp:
        content_bytes = input_fp.read().strip()
    soap_envelope = etree.fromstring(content_bytes)
    soap_body = match_xpath(soap_envelope, '//soap:Body')
    fiverx_root, = tuple(soap_body)

    fiverx_tag = fiverx_root.tag
    match = re.match('\{(.+)\}(.+)', fiverx_tag)
    ns_qualifier, tag_name = match.groups()

    if tag_name == 'sendeRezepte':
        rze_leistung, rze_param_version = tuple(fiverx_root)
        fiverx_xml = rze_leistung.text
    else:
        assert (tag_name == 'sendeRezepteResponse')
        fiverx_container, = tuple(fiverx_root)
        fiverx_xml = fiverx_container.text

    result = validate_payload(fiverx_xml)
    if not result:
        xml_color = TermColor.Fore.RED
        error_color = (TermColor.Style.BRIGHT + xml_color) if is_colorama_available else None
        with textcolor(error_color):
            print('invalid fiverx xml:')
            for error in result.errors:
                print('    ' + str(error))
        return

    xml = prettify_xml(fiverx_xml)
    print(xml)
