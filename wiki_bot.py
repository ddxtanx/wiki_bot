"""Generate a random page from a wikipedia category."""
import argparse
import logging
import random
from typing import Dict, List, Set, Iterable, Optional
from time import sleep

import requests as r


def wrapped_request(wiki_obj: str, mode: str) -> List[Dict[str, str]]:
    """Wrap a request to deal with connection errors.

    :param wiki_obj: name of page or category to process
    :param mode: type of pages to retrieve; one of "Subcat",
                 "Subpage", "Pagecats"
    :returns: MediaWiki API response data
    """

    def build_params():
        if mode == "pagecats":
            params = {
                "format": "json",
                "action": "query",
                "titles": wiki_obj,
                "prop": "categories"
            }
            return params

        if mode == "subcat":
            cmtype = "subcat"
        elif mode == "subpage":
            cmtype = "page"
        else:
            raise ValueError("Unknown mode for wrapped_request.")

        params = {
            "format": "json",
            "action": "query",
            "list": "categorymembers",
            "cmtitle": wiki_obj,
            "cmtype": cmtype
        }
        return params

    user_agent = ("wiki_bot/1.2.1 (https://github.com/ddxtanx/wiki_bot; "
                  "gcc@ameritech.net)")

    params = build_params()

    max_attempts = 5
    for attempt in range(max_attempts):
        # TODO argparse this
        sleep(1)

        try:
            base_url = "https://en.wikipedia.org/w/api.php"
            resp: r.Response = r.get(base_url,
                                     headers={"Api-User-Agent": user_agent},
                                     params=params)
            resp_json = resp.json()

            if mode == "pagecats":
                for key in resp_json["query"]["pages"]:
                    return resp_json["query"]["pages"][key]["categories"]

            return resp_json["query"]["categorymembers"]
        except r.exceptions.ConnectionError as conn_error:
            err_type = type(conn_error).__name__
            logging.warning("Caught %s, retrying page %s... (attempt %d/%d)",
                            err_type, wiki_obj, attempt + 1, max_attempts)

    logging.warning("Failed to retrieve %s.", wiki_obj)
    return [{
        "title": wiki_obj
    }]


class WikiBot():
    """WikiBot Class."""

    def __init__(self, tree_depth: int, min_similarity: float):
        """
        Constructor.

        :param tree_depth: maximum tree depth to descend
        :param min_similarity: minimum similarity threshold
        """
        self.td = tree_depth
        self.sv = similarity_val

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
        yield category

        if depth < self.tree_depth:
            for subcat in wrapped_request(category, "subcat"):
                if subcat["title"] in visited:
                    logging.debug("Skipping already-visited subcategory %s",
                                  subcat["title"])
                else:
                    logging.debug("(depth %d) Discovered subcategory %s of %s",
                                  depth, subcat["title"], category)

                    yield from self.get_subcategories(subcat["title"],
                                                      depth=depth + 1,
                                                      visited=visited)

    def save_array(self, category: str, subcats: Set[str]) -> None:
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

    def subcategories_without_duplicates(self, category: str) -> Set[str]:
        """
        :param category: category to return subcategories of
        :returns: deduplicated list of subcategories of `category`
        """
        return set(self.get_subcategories(category))

    def retrieve_subcategories_from_location(self, category: str) -> Set[str]:
        """
        Get subcategories from file, or generate them from scratch.

        :param category: category to retrieve subcategories of
        :returns: set of subcategories
        """
        sub_cats: Set[str] = set()
        filename = "{category}_subcats.txt".format(category=category)
        try:
            with open(filename, 'r') as sub_cat_file:
                logging.info("Reading subcategories from %s...", filename)
                file_lines = sub_cat_file.readlines()
                file_d = int(file_lines[0].split(":")[1].replace("\n", ""))
                if(file_d < self.td):
                    subcats = self.subcategories_without_duplicates(category)
                    self.save_array(category, subcats)
                    return sub_cats
                for i in range(1, len(file_lines)):
                    line = file_lines[i]
                    sub_cats.add(line.replace("\n", ""))
                sub_cat_file.close()
        except IOError:
            logging.info("Building subcategory cache...")
            sub_cats = self.subcategories_without_duplicates(category)
        return sub_cats

    def check_similarity(self, wiki_obj: str, subcategories: Set[str]) -> bool:
        """
        Check the similarity of page/category to a list of subcategories.

        :param wiki_obj: page or category to check similarity of
        :param subcategories: set of subcategories to compare against

        :returns: whether `wiki_obj >= min_similarity`
        """
        page_cats = wrapped_request(wiki_obj, "pagecats")

        if len(page_cats) == 1:
            return self.check_similarity(page_cats[0]['title'], subcategories)

        points = 0.0
        for cat in page_cats:
            title = cat['title']
            if(title in subcategories):
                points += 1.0

        score = points / len(page_cats)
        logging.debug("%s has similarity %.2f", wiki_obj, score)

        return score >= self.min_similarity

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
        sub_cats: Set[str] = set()

        if not regen:
            sub_cats = self.retrieve_subcategories_from_location(category)
        if regen or not sub_cats:
            logging.debug("Building cache for %s", category)
            sub_cats = self.subcategories_without_duplicates(category)
        if save or regen:
            self.save_array(category, sub_cats)

        random_page = None
        valid_random_page = True
        cat = random.sample(sub_cats, 1)[0]

        logging.debug("Descending into category %s", cat)
        pages = wrapped_request(cat, "subpage")

        while (not random_page or not valid_random_page):
            try:
                random_page = random.choice(pages)
                title = random_page['title']
                if check:
                    logging.debug("Checking similarity of %s", title)
                    valid_random_page = self.check_similarity(title, sub_cats)
                    if(not valid_random_page):
                        pages.remove(random_page)

            except IndexError:
                logging.debug("%s has no pages, retrying...", cat)

                sub_cats.remove(cat)
                if len(sub_cats) == 0:
                    logging.error("No subcategories had any pages.")

                cat = random.sample(sub_cats, 1)[0]
                logging.debug("Descending into category %s", cat)
                pages = wrapped_request(cat, mode="Subpage")
        return random_page['title']


if(__name__ == "__main__"):
    parser = argparse.ArgumentParser(
        description="Get a random page from a wikipedia category"
    )
    parser.add_argument('category',
                        help="The category you wish to get a page from."
                        )
    parser.add_argument('--tree_depth',
                        nargs='?',
                        type=int,
                        default=4,
                        help="How far down to traverse the subcategory tree"
                        )
    parser.add_argument('--similarity',
                        nargs='?',
                        type=float,
                        default=.25,
                        help="What percent of page categories need to be " +
                        "in subcategory array. Must be used with -c/--check")
    parser.add_argument("-s",
                        "--save",
                        action="store_true",
                        help="Save subcategories to a file for quick re-runs"
                        )
    parser.add_argument("-r",
                        "--regen",
                        action="store_true",
                        help="Regenerate the subcategory file"
                        )
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="Print debug lines"
                        )
    parser.add_argument("-c",
                        "--check",
                        action="store_true",
                        help="After finding page check to see that it truly " +
                        "fits in category"
                        )
    args = parser.parse_args()
    category = args.category # type: str
    check = args.check # type: bool
    save = args.save # type: bool
    regen = args.regen # type: bool
    DEBUGGING = args.verbose

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

    print("https://en.wikipedia.org/wiki/" + wb.random_page("Category:" +
               category,
               save=save,
               regen=regen,
               check=check
            )
        )
