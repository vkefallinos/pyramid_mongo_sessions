import os


from setuptools import find_packages
from setuptools import setup

# manage package version
package_version = '1.0.1'


# get readme and changes
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.txt')) as text_file:
        README = text_file.read()
    with open(os.path.join(here, 'CHANGES.txt')) as text_file:
        CHANGES = text_file.read()
except IOError:
    README = CHANGES = ''

# set up requires
install_requires = ['mongoengine', 'pyramid>=1.3', 'pycrypto']
testing_requires = ['nose']
testing_extras = testing_requires + ['coverage']
docs_extras = ['sphinx']


def main():

    setup(
        name='pyramid_mongo_sessions',
        version=package_version,
        description='Pyramid web framework session factory backed by Mongo',
        long_description=README + '\n\n' + CHANGES,
        classifiers=[
            'Intended Audience :: Developers',
            "Framework :: Pyramid",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.3",
            "Programming Language :: Python :: 3.4",
            ],
        keywords='pyramid session mongo',
        author='Vasilis Kefallinos',
        author_email='vasilis@mist.io',
        url='https://github.com/vkefallinos/pyramid_mongo_sessions',
        license='FreeBSD',
        packages=find_packages(),
        #test_suite='pyramid_redis_sessions.tests',
        test_suite='nose.collector',
        include_package_data=True,
        zip_safe=False,
        tests_require=testing_requires,
        install_requires=install_requires,
        entry_points='',
        extras_require = {
            'testing': testing_extras,
            'docs': docs_extras,
            },
    )

if __name__ == '__main__':
    main()
