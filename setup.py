from setuptools import setup, find_packages

setup(
    name='debian-package-collector',
    description='Debian package collector to download .deb packages from new releases',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=find_packages(exclude=['tests']),
    scripts=['bin/debian-package-collector.py'],
    data_files=[('config', ['config/debian-package-collector.conf'])],
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=[
        'flask',
        'waitress',
        'tenacity',
        'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest',
        'debian-package-downloader@git+https://github.com/EffectiveRange/debian-package-downloader.git@latest',
    ],
)
