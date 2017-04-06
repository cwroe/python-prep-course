import six
from setuptools import setup
from setuptools.command.test import test as TestCommand

VERSION = '0.0.1'
TEST_REQUIREMENTS = [
    'six==1.10.0',
    'nose==1.3.7',
    'pytoml==0.1.7'
]
if six.PY2:
    TEST_REQUIREMENTS += ['pathlib==2.1.0']


class PyTest(TestCommand):
    user_options = []

    def initialize_options(self):
        TestCommand.initialize_options(self)

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import sys
        from run_tests import test_lessons_solutions
        program = test_lessons_solutions(exit=False)

        sys.exit(int(not program.success))


setup(
    name='rmotr-prep-course',
    version=VERSION,
    description=("Rmotr.com Prep Course Material"),
    url='http://github.com/rmotr-curriculum/prep-course',
    download_url=(
        "https://github.com/rmotr-curriculum/prep-course/tarball/{version}".format(
            version=VERSION)),
    author='rmotr.com',
    author_email='questions@rmotr.com',
    license='MIT',
    packages=["."],
    tests_require=[
        'nose==1.3.7',
        'pytoml==0.1.7',
        'colorlog==2.7.0'
    ],
    zip_safe=False,
    cmdclass={'test': PyTest},
)
