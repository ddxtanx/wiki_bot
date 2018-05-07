# WikiBot
Welcome to WikiBot! This is a small program to get a random page from a Wikipedia category AND it's subcategories (up to a specified depth).

# Installation
All you need to do it clone this repo and install the dependencies. Make sure you have Pip installed!

```bash
git clone https://github.com/ddxtanx/wikiBot
cd wikiBot
pip install -r
```

OR

```bash
pip install wikiBot
```
To use as an API

# Usage
`python wikiBot.py -h` shows the usage of the program.
```
usage: wikiBot.py [-h] [--tree_depth [TREE_DEPTH]] [--similarity [SIMILARITY]]
                  [-s] [-r] [-v] [-c]
                  category

Get a random page from a wikipedia category

positional arguments:
  category              The category you wish to get a page from.


optional arguments:
  -h, --help            show this help message and exit
  --tree_depth [TREE_DEPTH]
                        How far down to traverse the subcategory tree
  --similarity [SIMILARITY]
                        What percent of page categories need to be in
                        subcategory array. Must be used with -c/--check
  -s, --save            Save subcategories to a file for quick re-runs
  -r, --regen           Regenerate the subcategory file
  -v, --verbose         Print debug lines
  -c, --check           After finding page check to see that it truly fits in
                        category
```

Pro Tips:
* Use a tree_depth of 3 or 4, more than 4 will bring loosely relates categories into subcategories.
* Use a similarity of .25 or .33. If you want a higher similarity value then you might sacrifice other valid pages in
search for the PERFECT page.

If you're using it in your own Python code the best way to set it up is
```python
from wikiBot import WikiBot
wb = WikiBot({{Your preferred tree_depth}}, {{Your preferred similarity_val}})

"""
...
Your Awesome Code
...
"""

randomPage = wb.randomPage(category,...)
```

You can also change the tree depth and similarity_val by using `wb.td = {{ New Tree Depth}}` and `wb.sv = {{ New Similarity Val}}`

More info available by using `help(wikiBot)`
# How It Works
The most important part of this program is the Wikipedia API; it allows the program to gather all of the subcategories of a given category in a fast(ish) and usable manner, and to get the pages belonging to a given category. The bulk of my code focuses on iteratively getting the subcategories at a given depth in a tree, adding them to an array with all subcategories of a given 'parent' category, and continuing on in that fashion until there are no more subcategories or the program has fetched to the maximum tree depth allowed. i.e. if a subcategory chain went

Category A -> Category B -> Category C -> Category D -> ...

(-> denotes 'is a supercategory of')

and the maximum tree depth was 3, then the code would stop gathering subcategories for Category C,D,E...

After all subcategories of a given parent category have been amassed in some list L, the program randomly chooses a category C from L, finds the pages belonging to C, chooses a random page P from C and return the URL pointing to P. For speeds sake, after gathering all subcategories from a given parent category the program optionally saves all of them to a text file to find subcategories faster.


To determine how similar a page is to a category, the program first enumerates what categories the page selected belongs to. Then it loops through all of the found categories using a variable I will call A here. It then checks if A belongs to the subcategories generated by the 'parent' category, and computes a 'score' of that page. If it is >= than a prespecified value (Default is .5: half of all A's should be subcategories of parent category) then it is a valid subpage. If not, it removes that page from the category list and loops on.
# Contributions
I'm open to anyone contributing, especially if they know of a way to make this faster or take up less drive space for locally stored subcategories. Email me at gcc@ameritech.net and we can talk stuff out.
