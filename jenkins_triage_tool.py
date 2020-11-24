#!/usr/bin/env python

import argparse
import coloredlogs, logging
import os
from pathlib import Path, PurePath
import sys

from junitparser import JUnitXml, Failure, Error
import yaml

current_dir = Path()  # current dir

DEFAULT_NIGHTLY_JOB = 'Pipelines/integration-pipeline'
DEFAULT_FEATURE_JOB = 'Test_Tower_Yolo_Express'

TMP_RESULTS_FILE = '/tmp/test_results.xml'

parser = argparse.ArgumentParser(description='Filter results from stdin or a junit file using triage notes')
parser.add_argument('--notes', dest='triage_notes', required=True, help='Path to triage notes file')
parser.add_argument('--test-results', dest='test_results', help='Path to results file')
parser.add_argument('--verbose', '-v', action='count')

args = parser.parse_args()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

if args.verbose == 2:
    coloredlogs.install(level='DEBUG', logger=logger)
elif args.verbose == 1:
    coloredlogs.install(level='INFO', logger=logger)
else:
    coloredlogs.install(level='CRITICAL', logger=logger)

class Config:
    def __init__(self, triage_notes=None, test_results=None):
        self.triage_notes = triage_notes
        self.test_results = test_results

config = Config(args.triage_notes, args.test_results)

def load_triage_notes(path):
    logger.info(f'loading triage notes from {path}')
    data = None
    with open(path, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data

def load_junit_test_results(path):
    # parse xml junit results
    xml = JUnitXml.fromfile(path)
    failures = []
    for suite in xml:
        for case in suite:
            if case.result:
                if isinstance(case.result, (Failure, Error)):
                    failures.append(case.name)
    return failures

if __name__ == "__main__":
    load_triage_notes(config.triage_notes)

    # get test results
    failures = []
    if config.test_results:
        failures = load_triage_notes(config.test_results)
    else:
        # read from stdin
        logger.info('reading failures from stdin')
        import sys
        for line in sys.stdin:
            failures.append(line.strip())
        logger.info('finished reading from stdin')

    logger.debug('loaded failures:')
    for failure in failures:
        logger.debug(failure)

