"""Generate a random page from a wikipedia category."""
import argparse
import logging
import random
from typing import List, Iterable, Optional
from urllib.parse import quote

from wiki_requests import (request_subcategories,
                           request_subpages,
                           request_page_categories,
                           request_pageid_from_title)


def similarity(wiki_obj: str, subcategories: Iterable[str]) -> float:
    """
    Return the similarity of page/category to a list of subcategories.

    :param wiki_obj: page or category to check similarity of
    :param subcategories: set of subcategories to compare against

    :returns: similarity score for `wiki_obj`
    """
    page_cats = request_page_categories(wiki_obj)

    matching_cats = [cat for cat in page_cats if cat in subcategories]

    score = len(matching_cats) / len(page_cats)
    logging.debug("%s has score %.2f", wiki_obj, score)
    return score


class WikiBot():
    """WikiBot Class."""

    def __init__(self, tree_depth: int, min_similarity: float):
        """
        Constructor.

        :param tree_depth: maximum tree depth to descend
        :param min_similarity: minimum similarity threshold
        """
        self.tree_depth = tree_depth
        self.min_similarity = min_similarity
        self.use_titles = False

    def get_subcategories(self,
                          category: str,
                          depth: int = 0,
                          visited: Optional[List[str]] = None
                          ) -> Iterable[str]:
        """
        Get subcategories of a given subcategory.

        :param category: category to generate subcategories of
        :returns: list of subcategories
        """
        if visited is None:
            visited = []

        visited.append(category)
        yield str(category)

        if depth < self.tree_depth:
            for subcat in request_subcategories(category):
                wiki_obj = subcat["pageid"]

                if wiki_obj in visited:
                    logging.debug("Skipping already-visited subcategory %s",
                                  wiki_obj)
                else:
                    logging.debug("(depth %d) Discovered subcategory %s of %s",
                                  depth + 1, wiki_obj, category)

                    yield from self.get_subcategories(wiki_obj,
                                                      depth=depth + 1,
                                                      visited=visited)

    def save_array(self, category: str, subcats: Iterable[str]):
        """
        Write array to `{category}_subcats.txt`.
        TODO Add filename to argparse.

        :param category: root category
        :param subcats: list of subcategories to write
        """
        filename = "{category}_subcats.txt".format(category=category)
        logging.info("Writing subcategories to %s...", filename)

        with open(filename, 'w') as outfile:
            outfile.write("depth:" + str(self.tree_depth) + "\n")
            outfile.write("\n".join(subcats))

    def get_all_subcategories(self, category: str) -> List[str]:
        """
        :param category: category to return subcategories of
        :returns: deduplicated list of subcategories of `category`
        """
        return list(self.get_subcategories(category))

    def import_subcategories(self, category: str) -> List[str]:
        """
        Get subcategories from file, or generate them from scratch.

        :param category: category to retrieve subcategories of
        :returns: set of subcategories
        """
        filename = "{category}_subcats.txt".format(category=category)

        try:
            with open(filename, 'r') as cache_file:
                logging.info("Cache found at %s.", filename)
                file_lines = cache_file.read().splitlines()

                file_depth = int(file_lines[0].split(":")[1])
        except IOError:
            logging.info("Cache not found at %s.", filename)
            subcats = self.get_all_subcategories(category)
            return list(subcats)

        if file_depth < self.tree_depth:
            logging.info("Updating cache from depth %d to depth %d.",
                         file_depth, self.tree_depth)

            subcats = self.get_all_subcategories(category)
            self.save_array(category, subcats)

            return list(subcats)

        subcats = file_lines[1:]
        return subcats

    def random_page(self,
                    category: str,
                    save: bool,
                    regen: bool,
                    check: bool) -> str:
        """
        Generate a random page from a category.

        :param category: category to get page from
        :param save: whether to save subcategories to a file
        :param regen: whether to regenerate subcategory cache
        :param check: whether to check page similarity
        :returns: a random page belonging to `category` or to one of its
                  subcategories
        """
        if regen:
            logging.debug("Regenerating cache for %s", category)
            subcats = self.get_all_subcategories(category)
            self.save_array(category, subcats)
        else:
            subcats = self.import_subcategories(category)
            if save:
                self.save_array(category, subcats)

        random_page = None
        valid_random_page = True
        cat = random.sample(subcats, 1)[0]

        logging.debug("Descending into category %s", cat)
        pages = request_subpages(cat)

        while (not random_page or not valid_random_page):
            try:
                random_page = random.choice(pages)
                wiki_obj = random_page["pageid"]

                if check:
                    logging.debug("Checking similarity of %s", wiki_obj)
                    page_similarity = similarity(wiki_obj, subcats)
                    valid_random_page = page_similarity >= self.min_similarity
                    if not valid_random_page:
                        pages.remove(random_page)

            except IndexError:
                logging.debug("%s has no pages, retrying...", cat)

                subcats.remove(cat)
                if len(subcats) == 0:
                    logging.error("No subcategories had any pages.")

                cat = random.sample(subcats, 1)[0]
                logging.debug("Descending into category %s", cat)
                pages = request_subpages(cat)

        return random_page["title"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Retrieve a random page from a Wikipedia category, "
                     "including its subcategories.")
    )
    parser.add_argument("category",
                        help="the root category to retrieve from"
                        )
    parser.add_argument("--tree_depth",
                        nargs="?",
                        type=int,
                        default=4,
                        help="maximum depth to traverse the subcategory tree"
                        )
    parser.add_argument("--similarity",
                        nargs="?",
                        type=float,
                        default=.25,
                        help=("if used with --check, the minimum proportion "
                              "of page categories appearing in the list of "
                              "visited subcategories")
                        )
    parser.add_argument("-s", "--save",
                        action="store_true",
                        help="save subcategories to a file for quick reruns"
                        )
    parser.add_argument("-r",
                        "--regen",
                        action="store_true",
                        help="regenerate the subcategory file"
                        )
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="print debug lines"
                        )
    parser.add_argument("-c",
                        "--check",
                        action="store_true",
                        help="check similarity of a page before returning it"
                        )
    args = parser.parse_args()

    wb = WikiBot(args.tree_depth, args.similarity)

    if args.verbose:
        LOG_LEVEL = logging.DEBUG
    else:
        LOG_LEVEL = logging.INFO

    logging.basicConfig(format="%(levelname)s:%(message)s", level=LOG_LEVEL)

    if args.save:
        logging.debug("Caching to file...")
    if args.regen:
        logging.debug("Regenerating cache...")

    category_id = request_pageid_from_title("Category:" + args.category)

    random_page_title = wb.random_page(category_id,
                                       save=args.save,
                                       regen=args.regen,
                                       check=args.check)

    random_page_title = random_page_title.replace(" ", "_")
    print("https://en.wikipedia.org/wiki/" + quote(random_page_title))
