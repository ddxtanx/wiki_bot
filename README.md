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
```
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
# How It Works
The most important part of this program is the Wikipedia API; it allows the program to gather all of the subcategories of a given category in a fast(ish) and usable manner, and to get the pages belonging to a given category. The bulk of my code focuses on iteratively getting the subcategories at a given depth in a tree, adding them to an array with all subcategories of a given 'parent' category, and continuing on in that fashion until there are no more subcategories or the program has fetched to the maximum tree depth allowed. i.e. if a subcategory chain went

Category A -> Category B -> Category C -> Category D -> ...

(-> denotes 'is a supercategory of')

and the maximum tree depth was 3, then the code would stop gathering subcategories for Category C,D,E...

After all subcategories of a given parent category have been amassed in some list L, the program randomly chooses a category C from L, finds the pages belonging to C, chooses a random page P from C and return the URL pointing to P. For speeds sake, after gathering all subcategories from a given parent category the program optionally saves all of them to a text file to find subcategories faster.

# Contributions
I'm open to anyone contributing, especially if they know of a way to make this faster or take up less drive space for locally stored subcategories. Email me at gcc@ameritech.net and we can talk stuff out.
