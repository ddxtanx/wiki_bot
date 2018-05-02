# WikiBot
Welcome to WikiBot! This is a small program to get a random page from a Wikipedia category AND it's subcategories (up to a specified depth).

# Installation
All you need to do it clone this repo and install the dependencies. Make sure you have Pip installed!

```bash
git clone https://github.com/ddxtanx/wikiBot
cd wikiBot
pip install -r
```

# Usage
`python wikiBot.py -h` shows the usage of the program.
```bash
usage: wikiBot.py [-h] [--tree_depth [TREE_DEPTH]] [-s] [-r] [-v] category

Get a random page from a wikipedia category.

positional arguments:
  category              The category you wish to get a random page from.

optional arguments:
  -h, --help            show this help message and exit
  --tree_depth [TREE_DEPTH]
                        How far down to traverse the subcategory tree
  -s, --save            Save subcategories to a file for quick re-runs
  -r, --regen           Regenerate the subcategory file
  -v, --verbose         Print debug lines
```

# Contributions
I'm open to anyone contributing, especially if they know of a way to make this faster or take up less drive space for locally stored subcategories. Email me at gcc@ameritech.net and we can talk stuff out.
