# wiki\_bot
WikiBot retrieves a random page from a given Wikipedia category, including its
subcategories.

## Install
From pip:
```bash
pip install wiki_bot
```

Locally:
```bash
git clone https://github.com/ddxtanx/wiki_bot
cd wiki_bot
pip install -r
```

## Usage
For best results:
- Set `tree_depth` to 3 or 4. Higher values tend to pull in loosely-related
  categories.
- Set `min_similarity` to 0.25 or 0.33. Higher values are likely to return
  relatively few results.

### CLI
```bash
$ python wiki_bot.py -h

usage: wiki_bot.py [-h] [--tree_depth [TREE_DEPTH]]
                   [--similarity [SIMILARITY]] [-s] [-r] [-v] [-c]
                   category

Retrieve a random page from a Wikipedia category, including its subcategories.

positional arguments:
  category              the root category to retrieve from

optional arguments:
  -h, --help            show this help message and exit
  --tree_depth [TREE_DEPTH]
                        maximum depth to traverse the subcategory tree
  --similarity [SIMILARITY]
                        if used with --check, the minimum proportion of page
                        categories appearing in the list of visited
                        subcategories
  -s, --save            save subcategories to a file for quick reruns
  -r, --regen           regenerate the subcategory file
  -v, --verbose         print debug lines
  -c, --check           check similarity of a page before returning it
```

### Module
```python
from wiki_bot import WikiBot
wb = WikiBot(tree_depth, similarity_val)

random_page = wb.randomPage(category,...)
```

## Implementation details
We use the [MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page) to
recursively retrieve subcategories of and pages belonging to a given category.
The parameter `tree_depth` denotes the maximum depth at which we traverse the
category tree. We optionally cache the retrieved list of categories. We then
select a category at random, select a page from that category at random, and
return that page's URL.

To prevent selection of unrelated pages, we optionally check the similarity of
a given page to the requested category by comparing the proportion of the
page's categories that are also subcategories of the requested category to a
user-specified threshold `min_similarity.`

## Contributing
Ensure that mypy, flake8, and pylint checks pass, then open a PR or contact
`gcc@ameritech.net.`
