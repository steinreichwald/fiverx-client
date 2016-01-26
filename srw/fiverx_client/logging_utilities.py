# -*- coding: utf-8 -*-

import logging
import os


___all__ = ['build_logger', 'null_logger']

class NullHandler(logging.Handler):
    def emit(self, record):
        pass

null_logger = logging.Logger('NullLogger')
null_logger.addHandler(NullHandler())

def configure_logging(log_filename, logger_name):
    logger = logging.Logger(logger_name)
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter and add it to the handlers
#    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # add the handlers to logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

def build_logger(data_filename, logger_name=None):
    path_basename, extension = os.path.splitext(data_filename)
    log_filename = path_basename + '.log'
    print(log_filename)
    basename = os.path.basename(path_basename)
    return configure_logging(log_filename, logger_name or basename)

