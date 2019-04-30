"""
srwlink-client

Usage:
  srwlink-client [--config=<config>] (ladeRzVersion|ladeRzDienste) [--chunked]
  srwlink-client -h --help
"""

from configparser import ConfigParser
from pathlib import Path
import sys

from docopt import docopt
from lxml import etree

from .soapclient import extract_response_payload, ladeRzDienste, ladeRzVersion, send_request
from .utils import pprint_xml


__all__ = ['client_main']

def client_main(argv=sys.argv):
    arguments = docopt(__doc__, argv=argv[1:])
    settings = load_settings(arguments)
    if not settings:
        return
    run_command(settings, arguments)

def run_command(settings, arguments):
    use_chunking = arguments['--chunked'] or False
    ws_url = settings['url']
    _s = settings
    header_params = {
        'user': _s['soap_user'],
        'password': _s['soap_password'],
        'apoik': _s['soap_apoik'],
    }

    for module in (ladeRzVersion, ladeRzDienste):
        command = module.__name__.rsplit('.', 1)[-1]
        if arguments[command]:
            soap_builder = getattr(module, 'build_soap_xml')
            soap_xml = soap_builder(header_params)
            payload_xpath = getattr(module, 'response_payload_xpath')
            break
    else:
        raise AssertionError('unexpected command')
    response = send_request(ws_url, soap_xml, use_chunking)
    print_soap_response(response, payload_xpath)

def load_settings(arguments):
    config_path = guess_config_path(arguments['--config'])
    if config_path is None:
        return
    settings = parse_config(config_path)
    return settings

def guess_config_path(config_path=None):
    if config_path:
        ini_path = Path(config_path)
    else:
        this_dir = Path('.')
        ini_files = tuple(this_dir.glob('*.ini'))
        nr_ini_files = len(ini_files)
        if nr_ini_files == 0:
            sys.stderr.write('No configuration files found (*.ini), please use --config=...\n')
            return None
        elif nr_ini_files == 1:
            ini_path = ini_files[0]
        else:
            sys.stderr.write('Multiple configuration files found (*.ini), please use --config=...\n')
            return None
    # .resolve() -- absolute path, no relative components (i.e. "..")
    # str() -- convert Path -> plain str which can be used by all other modules
    return str(ini_path.resolve())

def parse_config(config_path):
    config = ConfigParser()
    config.read([config_path])
    settings = dict(config.items('srw.link'))
    return settings

def print_soap_response(response, payload_xpath):
    if response.status_code != 200:
        print('Status Code: %r' % response.status_code)
    response_body = response.text
    contains_xml = response_body.startswith('<')
    if contains_xml:
        root = etree.fromstring(response_body)
        payload_xml_str = extract_response_payload(root, payload_xpath)
        pprint_xml(payload_xml_str or response_body)
    else:
        print(response_body)
