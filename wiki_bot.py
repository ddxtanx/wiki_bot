"""Generate a random page from a wikipedia category."""
import argparse
import random
from typing import Dict, List, Set

import requests

DEBUGGING = False
max_depth = 4
similarity_val = .5


def print_debug(debug_str: str) -> None:
    """Print strings if in debug/verbose mode mode.

    Input:
        Debug_Str (String): string to be printed
    Output:
        None
    Affect:
        If in debug mode, print Debug_Str
    """
    if DEBUGGING:
        print("DEBUG: " + debug_str)


def generate_requests_params(wiki_obj: str, mode: str) -> Dict[str, str]:
    """Generate the params for requests given a category and a mode.

    See wrapped_request for variable descriptions
    """
    cmtype = ""
    if mode == "Subcat":
        cmtype = 'subcat'
    elif mode == "Subpage":
        cmtype = 'page'
    params = {
        'format': 'json',
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': wiki_obj,
        'cmtype': cmtype
    }
    if mode == "Pagecats":
        params = {
            'format': 'json',
            'action': 'query',
            'titles': wiki_obj,
            'prop': 'categories'
        }
    return params

def wrapped_request(wiki_obj: str, mode: str) -> List[Dict[str,str]]:
    """Wrap a request to deal with connection errors.

    Input:
        wiki_obj (String):
            Page or category to process
        mode (String):
            Subcat: generate subcategories of a given category
            Subpage: generate subpages of a given category
            Pagecats: generate categories that page belongs to
    Output:
        List<String>: wikipedia API data for given request
    """
    header = "Garrett Credi's Random Page Bot(Contact @ gcc@ameritech.net)"
    header_val = {'Api-User-Agent': header}
    base_url = 'https://en.wikipedia.org/w/api.php'
    params = generate_requests_params(wiki_obj, mode)
    max_times = 5
    times = 0
    property_string = 'categorymembers'
    while times < max_times:
        try:
            req = requests.get(base_url, headers=header_val, params=params) #type: requests.Response
            reqJson = req.json()
            if mode != "Pagecats":
                return reqJson['query'][property_string]
            else:
                for key in reqJson['query']['pages']:
                    return reqJson['query']['pages'][key]['categories']
        except requests.exceptions.ConnectionError:
            print_debug(
                "Retrying {w} due to connection error".format(w=wiki_obj)
            )
            times += 1
    print_debug(
        "{w} failed too many times ({t}) times. " +
        "Moving on".format(
            w=wiki_obj,
            t=times
        )
    )
    times = 0
    return [{
        'title': wiki_obj
    }]


class WikiBot():
    """WikiBot Class."""

    def __init__(self, tree_depth: int, similarity_val: float) -> None:
        """Init Method for WikiBot.

        Input:
            Tree_Depth <Natural Number>
            SimilarityVal <Float>
        """
        self.td = tree_depth
        self.sv = similarity_val

    def get_subcategories(self, category: str) -> List[str]:
        """Get subcategories of a given subcategory.

        Input:
            Category (String): category to generate subcats of
        Output:
            List<Strings>: list of subcategories
        """
        current_depth = 1
        single_step_subcategories = [category]
        all_subcategories = []
        while current_depth <= self.td:
            print_debug("Current tree depth {d}".format(d=current_depth))
            subcategory_temp = []
            if not single_step_subcategories:
                break
            for subcat in single_step_subcategories:
                all_subcategories.append(subcat)
                subcategories = wrapped_request(subcat, "Subcat")
                for cat in subcategories:
                    title = cat['title']
                    print_debug("{subcat} has subcategory {title}".format(
                        subcat=subcat,
                        title=title
                    )
                    )
                    if title not in all_subcategories:
                        all_subcategories.append(title)
                        subcategory_temp.append(title)
                    else:
                        print_debug(
                            "{t} already checked. Moving on".format(t=title)
                        )
            single_step_subcategories = subcategory_temp
            current_depth += 1
        return all_subcategories

    def save_array(self, category: str, subcats: Set[str]) -> None:
        """Save array to file.

        Input:
            Category: category that subcats belong to
            Subcats List<String>: subcats of category
        Output:
            None
        Affect:
            If user has requisite permissions, subcategory list is saved
            to {category}_subcats.txt
        """
        filename = "{category}_subcats.txt".format(category=category)
        print_debug("Saving to {f}".format(f=filename))
        with open(filename, 'w') as f:
            f.write("td:" + str(self.td) + "\n")
            for cat in subcats:
                f.write(cat + "\n")

    def subcategories_without_duplicates(self, category: str) -> Set[str]:
        """Generate a list of subcategories without duplicates.

        Input:
            Subcats List<String>: list of subcategories
        Output:
            Set<String>: set of subcategories without any duplicates
        """
        return set(self.get_subcategories(category))

    def retreive_subcategories_from_location(self, category: str) -> Set[str]:
        """Get subcategories from file, or generate them from scratch.

        Input:
            Category (String): category to retreive subcats from.
        Output:
            Set<String>: set of subcategories
        """
        sub_cats = set() # type: Set[str]
        file_name = "{category}_subcats.txt".format(category=category)
        try:
            with open(file_name, 'r') as sub_cat_file:
                print_debug("Reading from {f}".format(f=file_name))
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
        except IOError as io_error:
            print_debug(
                "{f} does not exist. Building from network".format(f=file_name)
            )
            sub_cats = self.subcategories_without_duplicates(category)
        return sub_cats

    def check_similarity(self, wiki_obj: str, subcategories: Set[str]) -> bool:
        """Check the similarity of page/category to a list of subcategories.

        Input:
            Wiki_Obj (String): page or category to check similarity of
            Subcategories (Set<String>): set of subcategories
        Output:
            Boolean: whether or not wiki_obj is similar enough to subcategories
        """
        page_cats = wrapped_request(wiki_obj, mode="Pagecats")
        points = 0.0
        # For every supercategory of page, if it is also in subcategories
        # the page is more likely to be a true subpage.
        if(len(page_cats) == 1):
            return self.check_similarity(page_cats[0]['title'], subcategories)
        for cat in page_cats:
            title = cat['title']
            if(title in subcategories):
                points += 1.0
        score = points / len(page_cats)
        print_debug("Score of {w} is {s}".format(w=wiki_obj, s=str(score)))
        if(score >= self.sv):
            return True
        return False

    def random_page(self, category: str, save: bool, regen: bool, check: bool) ->str:
        """Generate a random page from a category.

        Input:
            Category (String): category to get page from
            Save (Boolean): whether or not to save subcategories to a file
            Regen (Boolean): whether or not to regenerate subcategory set
            Check (Boolean): whether or not to check page similarity
        Output:
            String: A random page belonging to category, or one of its subcats
        """
        sub_cats = set() # type: Set[str]
        if(not regen):
            sub_cats = self.retreive_subcategories_from_location(category)
        if(regen or (not sub_cats)):
            print_debug("Rebuilding {category}".format(category=category))
            sub_cats = self.subcategories_without_duplicates(category)
        if(save or regen):
            self.save_array(category, sub_cats)
        random_page = None
        valid_random_page = True
        cat = random.sample(sub_cats, 1)[0]
        print_debug("Chose category {cat}".format(cat=cat))
        pages = wrapped_request(cat, mode="Subpage")
        while(not random_page or not valid_random_page):
            try:
                random_page = random.choice(pages)
                title = random_page['title']
                if(check):
                    print_debug("Checking " + title)
                    valid_random_page = self.check_similarity(title, sub_cats)
                    if(not valid_random_page):
                        pages.remove(random_page)
            except IndexError as a:
                print_debug("{cat} has no pages. Retrying".format(cat=cat))
                sub_cats.remove(cat)
                if(len(sub_cats) == 0):
                    print_debug("No categories left. Sorry!")
                    raise ValueError("Category inputted is invalid.")
                cat = random.sample(sub_cats, 1)[0]
                print_debug("Chose category {cat}".format(cat=cat))
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
                        default=.5,
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
    max_depth = args.tree_depth
    similarity_val = args.similarity
    wb = WikiBot(max_depth, similarity_val)
    if(save):
        print_debug("Saving!")
    if(regen):
        print_debug("Regenerating!")

    print("https://en.wikipedia.org/wiki/" + wb.random_page("Category:" +
               category,
               save=save,
               regen=regen,
               check=check
            )
        )
