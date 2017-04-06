import unittest
import hashlib
import os
import sys

import logging
import logging.config
d = {
    'version': 1,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        },
        'colored': {
            '()': 'colorlog.ColoredFormatter',
            'format': "%(log_color)s%(levelname)-6s%(reset)s %(message)s %(blue)s\"%(lesson_name)s\""
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'colored',
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO'
        }
    }
}
logging.config.dictConfig(d)
logger = logging.getLogger(__name__)
try:
    from tempfile import TemporaryDirectory
except ImportError:
    import tempfile
    import shutil

    class TemporaryDirectory(object):
        def __enter__(self):
            self.dir_name = tempfile.mkdtemp()
            return self.dir_name

        def __exit__(self, exc_type, exc_value, traceback):
            shutil.rmtree(self.dir_name)

from nose.core import TestProgram
try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


import pytoml as toml

CODE_TYPE = 'code'
SOLUTIONS_RELATIVE_PATH = 'solutions'
TESTS_FILE_NAME = 'tests.py'


class InvalidLessonException(Exception):
    pass


class Lesson(object):
    def __init__(self, name, uuid, path, _lesson_data):
        self.name = name
        self.uuid = uuid
        self.path = path
        self._lesson_data = _lesson_data
        self.__test_data = None

    @property
    def test_data(self):
        if not self.__test_data:
            self.__test_data = read_lesson_tests(self.path)

        return self.__test_data


class Solution(object):
    def __init__(self, lesson, path):
        self.lesson = lesson
        self.path = path


def read_lesson_tests(lesson_path):
    tests_path = lesson_path / TESTS_FILE_NAME
    with tests_path.open('r') as tests_f:
        return tests_f.read()

def _get_unit_number(unit_name):
    start = unit_name.index('-') + 1
    end = unit_name.index('-', start)
    return int(unit_name[start:end])


def iter_code_lessons(path='.', unit_glob='unit-*', grep=None, units=None,
                      lesson_glob='lesson-*', rmotr_toml_name='.rmotr'):
    grep = grep or []

    p = Path(path)
    for unit in p.glob(unit_glob):
        unit_number = _get_unit_number(unit.name)
        if units and unit_number not in units:
            continue
        for lesson_path in unit.glob(lesson_glob):
            rmotr_toml = lesson_path / rmotr_toml_name
            if not rmotr_toml.exists():
                raise InvalidLessonException(
                    ("Lessons must contain a .rmotr file. "
                     "Lesson {} doesn't contain any").format(lesson_path.name))

            with rmotr_toml.open() as rmotr_f:
                lesson_data = toml.load(rmotr_f)
                lesson_name = lesson_data['name']
                if lesson_data['type'] == 'assignment':
                    add_lesson = True
                    for keyword in grep:
                        if keyword not in lesson_name.lower():
                            add_lesson = False
                            break
                    if not add_lesson:
                        continue
                    logger.info("Added lesson", extra={'lesson_name': lesson_name})
                    yield Lesson(name=lesson_name,
                                 uuid=lesson_data['uuid'],
                                 path=lesson_path,
                                 _lesson_data=lesson_data)


def iter_lesson_solutions(lesson):
    solutions_path = (lesson.path / SOLUTIONS_RELATIVE_PATH)
    if solutions_path.exists():
        for solution_path in solutions_path.glob('*.py'):
            yield Solution(lesson=lesson, path=solution_path)


def write_solution_test_file(_dir, solution):
    abs_path = os.path.abspath(_dir)

    lesson_hash = hashlib.md5(
        str(solution.lesson.path).encode('utf-8')).hexdigest()

    test_file_name = "test_{hash}_{solution}".format(
        solution=solution.path.name, hash=lesson_hash)
    test_file_path = os.path.join(abs_path, test_file_name)
    with open(test_file_path, 'w') as test_f, solution.path.open('r') as solution_f:
        test_f.write(solution_f.read())
        test_f.write('\n\n')
        test_f.write(solution.lesson.test_data)


def test_lessons_solutions(grep=None, units=None, exit=True):

    with TemporaryDirectory() as temp_dir:
        abs_path = os.path.abspath(temp_dir)
        for lesson in iter_code_lessons(grep=grep, units=units):
            for solution in iter_lesson_solutions(lesson):
                write_solution_test_file(temp_dir, solution)

        suite = unittest.TestLoader().discover(abs_path)
        program = TestProgram(suite=suite, exit=False, argv=sys.argv[0:1])

        if exit:
            sys.exit(int(not program.success))

        return program


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run tests')
    parser.add_argument('-g', '--grep', nargs='+', required=False)
    parser.add_argument('-u', '--units', nargs='+', type=int, required=False)
    parser.add_argument('-v', '--verbose', action='store_true', required=False)
    args = parser.parse_args()
    if not args.verbose:
        logger.setLevel('ERROR')

    test_lessons_solutions(grep=args.grep, units=args.units)
