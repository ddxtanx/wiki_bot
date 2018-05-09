from setuptools import setup

with open('README.md') as f:
    long_description = f.read()
setup(
  name='wiki_bot',
  version='1.3.1',
  description='A random wikipedia page generator.',
  long_description=long_description,
  long_description_content_type="text/markdown",
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
