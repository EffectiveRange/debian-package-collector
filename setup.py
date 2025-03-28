from setuptools import setup

setup(
    name='debian-package-collector',
    version='1.2.1',
    description='Debian package collector to download .deb packages from new releases',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=['package_collector'],
    scripts=['bin/debian-package-collector.py'],
    data_files=[('config', ['config/debian-package-collector.conf'])],
    install_requires=[
        'flask',
        'waitress',
        'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest',
        'debian-package-downloader@git+https://github.com/EffectiveRange/debian-package-downloader.git@latest',
    ],
)
