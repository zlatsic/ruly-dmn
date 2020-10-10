import setuptools


with open('README.md', 'r') as fh:
    long_description = fh.read()
with open('version.txt', 'r') as fh:
    version = fh.read()[:-1]

setuptools.setup(
    name='ruly-dmn',
    packages=['ruly_dmn'],
    version=version,
    url='https://github.com/ZlatSic/ruly-dmn',
    author='Zlatan Sičanica',
    author_email='zlatan.sicanica@gmail.com',
    description='DMN implementation with ruly rule engine',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities'
    ],
    entry_points={
        'console_scripts': [
            'ruly-dmn = ruly_dmn.main:main'
        ]
    },
    install_requires=[
        'ruly',
    ]
)
