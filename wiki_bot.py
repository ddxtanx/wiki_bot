"""Retrieve a random page from a given Wikipedia category, including its
subcategories.
"""
import argparse
import json
import logging
import random
from typing import List, Dict, Iterable, Optional
from urllib.parse import quote

import requests as r  # pylint:disable=import-error

from wiki_requests import (JSON,
                           request_category_info,
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

    def __init__(self, tree_depth: int = 4, min_similarity: float = 0, verbose: bool = False):
        """
        Constructor.

        :param tree_depth: maximum tree depth to descend
        :param min_similarity: minimum similarity threshold
        """
        self.tree_depth = tree_depth
        self.min_similarity = min_similarity

        if verbose:
            LOG_LEVEL = logging.DEBUG
        else:
            LOG_LEVEL = logging.INFO

        logging.basicConfig(format="%(levelname)s:%(message)s", level=LOG_LEVEL)


    def get_subcategories(self,
                          category_id: str,
                          depth: int = 0,
                          visited: Optional[List[str]] = None,
                          parent: str = None
                          ) -> Iterable[JSON]:
        """
        Get subcategories of a given subcategory.

        :param category_id: id of category to generate subcategories of
        :returns: list of subcategories
        """
        if visited is None:
            visited = []

        visited.append(category_id)

        if depth < self.tree_depth:
            category_info = request_category_info(category_id)

            page_count: int = category_info["page_count"]
            yield {category_id: {"page_count": page_count,
                                 "depth": depth,
                                 "parent": parent}}

            for subcat in category_info["subcats"]:
                subcat_id = subcat["pageid"]
                subcat_name = subcat["title"]

                if subcat_id in visited:
                    logging.debug("Skipping already-visited category %s",
                                  subcat_name)
                else:
                    logging.debug("(depth %d) Discovered category %s",
                                  depth + 1, subcat_name)

                    yield from self.get_subcategories(subcat_id,
                                                      depth=depth + 1,
                                                      visited=visited,
                                                      parent=category_id)

    def save_array(self, category: str, subcats: Iterable[str]):
        """
        Write array to `{category}_subcats.json`.
        TODO Add filename to argparse.

        :param category: root category
        :param subcats: list of subcategories to write
        """
        filename = "{category}_subcats.json".format(category=category)
        logging.info("Writing subcategories to %s...", filename)

        with open(filename, 'w') as outfile:
            json.dump(subcats, outfile)

    def get_all_subcategories(self, category: str) -> Dict[str, int]:
        """
        :param category: category to return subcategories of
        :returns: deduplicated list of subcategories of `category`
        """
        subcats = {}
        try:
            for subcat in self.get_subcategories(category):
                subcats.update(subcat)
        except r.exceptions.ConnectionError as conn_error:
            logging.error("Connection error. Saving...")
            self.save_array(category, subcats)
            raise conn_error

        return subcats

    def import_subcategories(self, category: str) -> Dict[str, int]:
        """
        Get subcategories from file, or generate them from scratch.

        :param category: category to retrieve subcategories of
        :returns: set of subcategories
        """
        filename = "{category}_subcats.json".format(category=category)

        try:
            with open(filename, 'r') as cache_file:
                logging.info("Cache found at %s.", filename)
                subcats = json.load(cache_file)

                file_depth = 1 + max(data["depth"] for data in subcats.values())
        except (FileNotFoundError, IOError):
            logging.info("Cache not found at %s.", filename)
            subcats = self.get_all_subcategories(category)
            return subcats

        if file_depth < self.tree_depth:
            logging.info("Updating cache from depth %d to depth %d.",
                         file_depth, self.tree_depth)

            subcats = self.get_all_subcategories(category)
            self.save_array(category, subcats)

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

        while subcats:
            subcat_names = list(subcats.keys())

            subcat_freqs = [data["page_count"] for data in subcats.values()]
            category = random.choices(subcat_names, weights=subcat_freqs)[0]

            logging.debug("Trying category %s", category)
            pages = request_subpages(category)

            try:
                found_match = False
                while not found_match:
                    random_page = random.choice(pages)
                    page_id = random_page["pageid"]

                    page_similarity = similarity(page_id, subcats)
                    if check and page_similarity < self.min_similarity:
                        del subcats[category]
                        pages.remove(random_page)
                    else:
                        found_match = True

                return random_page["title"]
            except IndexError:
                logging.debug("%s has no matching pages.", category)
                subcat_names.remove(category)

        raise ValueError("Couldn't find any matching pages.")


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

    wb = WikiBot(tree_depth=args.tree_depth, min_similarity=args.similarity, verbose=args.verbose)

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
