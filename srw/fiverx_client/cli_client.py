"""
srwlink-client

Low-level client to send SOAP requests to a fiverx server.

Usage:
  srwlink-client [options] <command> [<args>...]

Options:
  --chunked        Use chunked HTTP requests
  --no-cert-verification disable TLS certificate verification
  --config=<config> Specify config file
  --print-request  Also print the request payload
  -h, --help       Show this screen
  --test           Set "test" flag

Subcommands:
"""
# subcommand names are added automatically

import cgi
from configparser import ConfigParser
from pathlib import Path
import sys

from docopt import docopt, DocoptExit
from lxml import etree

from . import soapclient
from .utils import (is_colorama_available, parse_command_args, prettify_xml,
    strip_xml_encoding, textcolor, TermColor)


__all__ = ['client_main']

def client_main(argv=sys.argv):
    submodules = [getattr(soapclient, c) for c in sorted(dir(soapclient))]
    available_subcommands = [m for m in submodules if hasattr(m, 'build_soap_xml')]
    subcommand_names = [m.__name__.rsplit('.', 1)[-1] for m in available_subcommands]
    # add all available subcommands to __doc__ so we never have to list them
    # explicitely
    indent = lambda s: '    ' + s
    client_doc = __doc__ + '\n'.join(map(indent, subcommand_names))

    # options_first=True is important to implement subcommands
    arguments = docopt(client_doc, argv=argv[1:], options_first=True)
    subcommand = arguments.pop('<command>')
    _cmd_args = arguments.pop('<args>') or ()
    # commands should be able to have their own parameters but I want that this
    # still works:
    #     srwlink-client --config=... ladeRzDienste --help
    if ('--help' in _cmd_args) or (subcommand == 'help'):
        docopt(client_doc, ('--help',))

    settings = load_settings(arguments)
    if not settings:
        return
    # remove some arguments which are handled by docopt ("--help") or not
    # needed anymore at this point ("--config") so we only have meaningful
    # keys in "arguments".
    del arguments['--config']
    del arguments['--help']

    cmd_module = None
    subcommand_modules = dict(zip(subcommand_names, available_subcommands))
    for command_name in subcommand_names:
        is_active_command = (subcommand == command_name)
        if is_active_command:
            module = subcommand_modules[command_name]
            cmd_module = module
    if cmd_module is None:
        raise DocoptExit('unexpected command')

    run_command(cmd_module, settings, arguments, _cmd_args)

def run_command(cmd_module, settings, global_args, command_args):
    use_chunking = global_args.pop('--chunked')
    is_test_request = global_args.pop('--test')
    print_request = global_args.pop('--print-request')
    verify_cert = not global_args.pop('--no-cert-verification')
    command_args = parse_command_args(cmd_module.__doc__, command_args, global_args)

    _s = settings
    header_params = {
        'user': _s['soap_user'],
        'password': _s['soap_password'],
        'apoik': _s['soap_apoik'],
        'test': 'true' if is_test_request else 'false',
    }
    soap_builder = getattr(cmd_module, 'build_soap_xml')
    soap_xml = soap_builder(header_params, command_args)

    if print_request:
        request_payload_xpath = guess_payload_xpath(soap_xml)
        print_soap_request(soap_xml, request_payload_xpath)
        print('-------------------------------------------------------------')
    ws_url = settings['url']
    response = soapclient.send_request(ws_url, soap_xml, use_chunking, verify_cert=verify_cert)
    mimetype, options = cgi.parse_header(response.headers['Content-Type'])
    if mimetype == 'text/html':
        with textcolor(TermColor.Fore.RED):
            print(f'HTML response: Status {response.status_code}')
            print(response.content)
    else:
        payload_xpath = getattr(cmd_module, 'response_payload_xpath')
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

def guess_payload_xpath(soap_xml):
    root = etree.fromstring(strip_xml_encoding(soap_xml))
    fiverx_root = soapclient.match_xpath(root, '//soap:Body/fiverx:*')
    assert fiverx_root is not None
    simple_name = fiverx_root.tag.split('}', 1)[-1]
    return '//soap:Body/fiverx:%s/*' % simple_name

def print_soap_request(soap_xml, payload_xpath):
    root = etree.fromstring(strip_xml_encoding(soap_xml))
    payload_xml_str = soapclient.extract_response_payload(root, payload_xpath)
    prettified_xml = prettify_xml(payload_xml_str)
    is_valid = soapclient.validate_payload(prettified_xml)
    xml_color = TermColor.Fore.GREEN if is_valid else TermColor.Fore.RED
    with textcolor(xml_color):
        print(prettified_xml)

def print_soap_response(response, payload_xpath):
    if response.status_code != 200:
        print('Status Code: %r' % response.status_code)
    response_body = response.text
    contains_xml = response_body.startswith('<')
    if contains_xml:
        # If the server response starts with an XML encoding declaration this
        # will lead to an lxml exception because "response_body" is already
        # a string. Just ignore the XML encoding by stripping it.
        try:
            root = etree.fromstring(strip_xml_encoding(response_body))
        except:
            with textcolor(TermColor.Fore.RED):
                print(response_body)
            return
        payload_xml_str = soapclient.extract_response_payload(root, payload_xpath)
        prettified_xml = prettify_xml(payload_xml_str or response_body)
        is_valid = soapclient.validate_payload(prettified_xml)
        xml_color = TermColor.Fore.GREEN if is_valid else TermColor.Fore.RED
        with textcolor(xml_color):
            print(prettified_xml)

        if not is_valid:
            error_color = (TermColor.Style.BRIGHT + xml_color) if is_colorama_available else None
            with textcolor(error_color):
                print('==> INVALID XML in server response!')
    else:
        print(response_body)
