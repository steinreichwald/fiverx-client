"""
srwlink-client

Low-level client to send SOAP requests to a fiverx server.

Usage:
  srwlink-client [options] <command> [<args>...]

Options:
  --chunked        Use chunked HTTP requests
  --no-cert-verification    disable TLS certificate verification
  --config=<config> Specify config file
  --print-request  Also print the request payload
  --api-version=<apoti_version>  Version of the ApoTI protocol [default: 01.08]
  --quiet          Suppress all output
  -h, --help       Show this screen
  --test           Set "test" flag

Exit codes:
  5    unable to load settings
 10    invalid request
 15    problem sending request
 21    unexpected content type in response
 22    response data is not well-formed XML
 23    invalid XML response (XML Schema)

Subcommands:
"""
# subcommand names are added automatically

import cgi
from configparser import ConfigParser
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from docopt import docopt, DocoptExit
from lxml import etree
from requests.exceptions import RequestException

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
        return 5
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
    api_version = global_args.pop('--api-version')
    assert (api_version in ('01.08', '01.10'))
    quiet = global_args.pop('--quiet')
    if quiet:
        assert (not print_request)
    command_args = parse_command_args(cmd_module.__doc__, command_args, global_args)

    _s = settings
    soap_user = _s.get('soap_user')
    apo_ik = _s.get('soap_apoik')
    assert (soap_user or apo_ik)
    if (not soap_user) and apo_ik:
        assert re.match('^\d{9}$', apo_ik)
        soap_user = apo_ik
    elif (not apo_ik) and soap_user:
        assert re.match('^\d{9}$', soap_user)
        apo_ik = soap_user

    header_params = {
        'user': soap_user,
        'password': _s['soap_password'],
        'apoik': apo_ik,
        'test': 'true' if is_test_request else 'false',
    }
    soap_builder = getattr(cmd_module, 'build_soap_xml')
    soap_xml = soap_builder(header_params, command_args, version=api_version)

    if print_request:
        request_payload_xpath = guess_payload_xpath(soap_xml)
        is_valid = print_soap_request(soap_xml, request_payload_xpath)
        if not is_valid:
            return 10
        print('-------------------------------------------------------------')
    ws_url = settings['url']
    hostname = settings.get('hostname')
    if not contains_hostname(ws_url):
        verify_cert = False
        if not hostname:
            with textcolor(TermColor.Fore.YELLOW):
                print(f'web service URL "{ws_url}" references specific IP address but no hostname set in config')
    elif hostname:
        url = urlparse(ws_url)
        if (hostname != url.hostname) and (not quiet):
            with textcolor(TermColor.Fore.YELLOW):
                print(f'Configured HTTP host name "{hostname}" does not match web service URL "{ws_url}"')
    try:
        response = soapclient.send_request(ws_url, soap_xml, use_chunking, verify_cert=verify_cert, hostname=hostname)
    except KeyboardInterrupt:
        # avoid ugly traceback when user cancels request with Ctrl+C
        if not quiet:
            with textcolor(TermColor.Fore.YELLOW):
                print('request cancelled')
        return 0
    except RequestException as e:
        if not quiet:
            with textcolor(TermColor.Fore.RED):
                print(f'unable to send request to {ws_url}:')
                print(str(e))
        return 15
    mimetype, options = cgi.parse_header(response.headers['Content-Type'])
    if mimetype == 'text/html':
        if not quiet:
            with textcolor(TermColor.Fore.RED):
                print(f'HTML response: Status {response.status_code} (text/html)')
                if not response.content:
                    content_length = response.headers.get('Content-Length')
                    print('no response body (header "Content-Length": %r)' % content_length)
                else:
                    print(response.content)
        return 21
    else:
        payload_xpath = getattr(cmd_module, 'response_payload_xpath')
        rc = process_soap_response(response, payload_xpath, quiet=quiet)
        return rc

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

def contains_hostname(url_str):
    url = urlparse(url_str)
    ipv4_regex = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    # url.hostname only contains the hostname/IP address without port
    contains_ipv4 = ipv4_regex.match(url.hostname)
    return not contains_ipv4

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
    match = re.search(r'&lt;versionNr&gt;(01\.\d{2})&lt;/versionNr&gt;', soap_xml)
    version = match.group(1)

    is_valid = soapclient.validate_payload(prettified_xml, version=version)
    xml_color = TermColor.Fore.GREEN if is_valid else TermColor.Fore.RED
    with textcolor(xml_color):
        print(prettified_xml)
    return is_valid

def process_soap_response(response, payload_xpath, *, quiet=False):
    if (response.status_code != 200) and not quiet:
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
            if not quiet:
                with textcolor(TermColor.Fore.RED):
                    print(response_body)
            return 22
        payload_xml_str = soapclient.extract_response_payload(root, payload_xpath)
        prettified_xml = prettify_xml(payload_xml_str or response_body)
        is_valid = soapclient.validate_payload(prettified_xml)
        xml_color = TermColor.Fore.GREEN if is_valid else TermColor.Fore.RED
        if not quiet:
            with textcolor(xml_color):
                print(prettified_xml)

        if not is_valid:
            if not quiet:
                error_color = (TermColor.Style.BRIGHT + xml_color) if is_colorama_available else None
                with textcolor(error_color):
                    print('==> INVALID XML in server response!')
            return 23
        return 0
    else:
        if not quiet:
            print(response_body)
        return 22
