from setuptools import setup

setup(
  name='wiki_bot',
  version='1.2',
  description='A random wikipedia page generator.',
  long_description='A bot that uses the Wikipedia API to enumerate ' +
  'subcategories and subpages to generate a random page that is a member of ' +
  'a given supercategory.',
  author='Garrett Credi',
  author_email='gcc@ameritech.net',
  url='https://github.com/ddxtanx/wiki_bot',
  license='MIT',
  download_url='https://github.com/ddxtanx/wiki_bot/archive/1.1.tar.gz',
  py_modules=["wiki_bot"],
  keywords=['wikipedia', 'random', 'generator', 'command_line', 'api', 'mypy', 'library', 'wiki'],
  classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Environment :: Console",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: MIT License",
      "Natural Language :: English",
      "Operating System :: OS Independent",
      "Programming Language :: Python :: 3.6",
      "Topic :: Internet :: WWW/HTTP :: Indexing/Search"
  ],
  install_requires=['requests', 'mypy']
)
