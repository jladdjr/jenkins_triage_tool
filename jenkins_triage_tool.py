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

class TriagedTest(object):
    def __init__(self, test):
        self.test = test

    @property
    def name(self):
        return self.test.get('name').strip()

    @property
    def description(self):
        return self.test.get('description').strip()

    def __str__(self):
        if self.description:
            return f'{self.name:20}   {self.description}'
        return f'{self.name}'

class TestSet(object):
    def __init__(self, tests):
        self.tests = [TriagedTest(test) for test in tests]

    def as_plain_list(self):
        res = []
        for test in self.tests:
            if not test.name:
                continue
            res.append(test.name)
        return res

    def __iter__(self):
        return self.tests.__iter__()

class TriageData(object):
    def __init__(self, path):
        self.tests = None
        self._load_triage_data(path)

    def _load_triage_data(self, path):
        logger.info(f'loading triage notes from {path}')
        data = None
        with open(path, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            self.tests = data['tests']

    def get_tests(self, label=None):
        if not label:
            return TestSet(self.tests)

        # filter by label
        res = []
        for test in self.tests:
            if test.get('label') == label:
                res.append(test)
        return TestSet(res)

    def get_test(self, name):
        """Return test matching name"""
        for test in self.tests:
            test_name = test.get('name').strip()
            if test_name == name:
                return test
        return None

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

def get_untriaged_failures(failures, triage_data):
    """Returns failures that are not listed in triage data"""
    res = [ ]
    for failure in failures:
        # skip any test that has been triaged
        if triage_data.get_test(failure):
            continue
        res.append(failure)
    return res

def get_unlabeled_failures(failures, triage_data):
    """Returns failures that have a triage entry
    without a label assigned"""
    res = [ ]
    for failure in failures:
        # skip any test that has been triaged
        match = triage_data.get_test(failure)
        if not match:
            continue
        if not match.get('label'):
            res.append(match)
    return TestSet(res)

def get_failures_marked_with_label(failures, triage_data, label):
    """Returns failures that have a triage entry
    assigned a given label"""
    res = [ ]
    for failure in failures:
        # skip any test that has been triaged
        match = triage_data.get_test(failure)
        if not match:
            continue
        if match.get('label') == label:
            res.append(match)
    return TestSet(res)

def list_failures_in_context(failures, triage_data):
    untriaged_failures = get_untriaged_failures(failures, triage_data) # raw list of failures
    unlabeled_failures = get_unlabeled_failures(failures, triage_data)
    true_failures = get_failures_marked_with_label(failures, triage_data, label='failing')
    flakey_tests = get_failures_marked_with_label(failures, triage_data, label='flake')

    print('Not Triaged')
    for failure in untriaged_failures:
        print(f'  {failure}')
    print()

    print('Partially Triaged')
    for failure in unlabeled_failures:
        print(f'  {failure}')
    print()

    print('True Failures')
    for failure in true_failures:
        print(f'  {failure}')
    print()

    print('Flakey Tests')
    for failure in flakey_tests:
        print(f'  {failure}')
    print()

if __name__ == "__main__":
    # get triage notes
    triage_data = TriageData(config.triage_notes)

    # get test results
    failures = []
    if config.test_results:
        failures = load_triage_data(config.test_results)
    else:
        # read from stdin
        logger.info('reading failures from stdin')
        import sys
        for line in sys.stdin:
            failures.append(line.strip())
        logger.info('finished reading from stdin')

    logger.debug('loaded failures:')
    for failure in failures:
        logger.debug(f'  {failure}')

    # print test failures
    # sorted by triage data
    list_failures_in_context(failures, triage_data)
