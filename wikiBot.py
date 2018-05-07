"""Generate a random page from a wikipedia category."""
import argparse
import random

import requests

DEBUGGING = False
max_depth = 4
similarityVal = .5


def print_debug(debug_str):
    """Print strings if in debug/verbose mode mode.

    Input:
        Debug_Str (String): string to be printed
    Output:
        None
    Affect:
        If in debug mode, print Debug_Str
    """
    global DEBUGGING
    if(DEBUGGING):
        print("DEBUG: " + debug_str)


class WikiBot():
    """WikiBot Class."""

    def __init__(self, tree_depth, similarity_val):
        """Init Method for WikiBot.

        Input:
            Tree_Depth <Natural Number>
            SimilarityVal <Float>
        """
        self.td = tree_depth
        self.sv = similarity_val


    def generateRequestsParams(self, wiki_obj, mode):
        """Generate the params for requests given a category and a mode.

        See wrappedRequest for variable descriptions
        """
        cmtype = ""
        if(mode == "Subcat"):
            cmtype = 'subcat'
        elif(mode == "Subpage"):
            cmtype = 'page'
        params = {
            'format': 'json',
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': wiki_obj,
            'cmlimit': 500,
            'cmtype': cmtype
        }
        if(mode == "Pagecats"):
            params = {
                'format': 'json',
                'action': 'query',
                'titles': wiki_obj,
                'prop': 'categories'
            }
        return params

    def wrappedRequest(self, wiki_obj, mode):
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
        headerVal = {'Api-User-Agent': header}
        base_url = 'https://en.wikipedia.org/w/api.php'
        params = self.generateRequestsParams(wiki_obj, mode)
        max_times = 5
        times = 0
        propertyString = 'categorymembers'
        while(times < max_times):
            try:
                r = requests.get(base_url, headers=headerVal, params=params)
                if(mode != "Pagecats"):
                    return r.json()['query'][propertyString]
                else:
                    for key in r.json()['query']['pages']:
                        return r.json()['query']['pages'][key]['categories']
            except requests.exceptions.ConnectionError as e:
                if(times > max_times):
                    print_debug(
                        "{w} failed too many times ({t}) times. " +
                        "Moving on".format(
                                    w=wiki_obj,
                                    t=times
                        )
                    )
                    times = 0
                    return [wiki_obj]
                else:
                    print_debug(
                        "Retrying {w} due to connection error".format(w=wiki_obj)
                    )
                    times += 1

    def getSubcategories(self, category):
        """Get subcategories of a given subcategory.

        Input:
            Category (String): category to generate subcats of
        Output:
            List<Strings>: list of subcategories
        """
        global max_depth, DEBUGGING
        current_depth = 1
        singleStepSubcategories = [category]
        allSubcategories = []
        while(current_depth <= self.td):
            print_debug("Current tree depth {d}".format(d=current_depth))
            subcategoryTemp = []
            if(len(singleStepSubcategories) == 0):
                break
            for subcat in singleStepSubcategories:
                allSubcategories.append(subcat)
                subcategories = self.wrappedRequest(subcat, mode="Subcat")
                for cat in subcategories:
                    title = cat['title']
                    print_debug("{subcat} has subcategory {title}".format(
                                    subcat=subcat,
                                    title=title
                                    )
                                )
                    if(title not in allSubcategories):
                        allSubcategories.append(title)
                        subcategoryTemp.append(title)
                    else:
                        print_debug(
                            "{t} already checked. Moving on".format(t=title)
                        )
            singleStepSubcategories = subcategoryTemp
            current_depth += 1
        return allSubcategories

    def saveArray(self, category, subcats):
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
            f.write("td:"+str(self.td)+"\n")
            for cat in subcats:
                f.write(cat+"\n")

    def subcategoriesWithoutDuplicates(self, subcats):
        """Generate a list of subcategories without duplicates.

        Input:
            Subcats List<String>: list of subcategories
        Output:
            Set<String>: set of subcategories without any duplicates
        """
        return set(self.getSubcategories(subcats))

    def retreiveSubcategoriesFromLocation(self, category):
        """Get subcategories from file, or generate them from scratch.

        Input:
            Category (String): category to retreive subcats from.
        Output:
            Set<String>: set of subcategories
        """
        subCats = []
        fileName = "{category}_subcats.txt".format(category=category)
        try:
            with open(fileName, 'r') as subCatFile:
                print_debug("Reading from {f}".format(f=fileName))
                fileLines = subCatFile.readlines()
                fileD = int(fileLines[0].split(":")[1].replace("\n", ""))
                if(fileD < self.td):
                    subcats = self.getSubcategories(category)
                    self.saveArray(category, subcats)
                    return subCats
                for i in range(1, len(fileLines)):
                    line = fileLines[i]
                    subCats.append(line.replace("\n", ""))
                subCatFile.close()
        except IOError as ioError:
            print_debug(
                "{f} does not exist. Building from network".format(f=fileName)
            )
            subCats = self.subcategoriesWithoutDuplicates(category)
        return subCats

    def checkSimilarity(self, wiki_obj, subcategories):
        """Check the similarity of page/category to a list of subcategories.

        Input:
            Wiki_Obj (String): page or category to check similarity of
            Subcategories (Set<String>): set of subcategories
        Output:
            Boolean: whether or not wiki_obj is similar enough to subcategories
        """
        pageCats = self.wrappedRequest(wiki_obj, mode="Pagecats")
        points = 0.0
        # For every supercategory of page, if it is also in subcategories
        # the page is more likely to be a true subpage.
        if(len(pageCats) == 1):
            return self.checkSimilarity(pageCats[0]['title'], subcategories)
        for cat in pageCats:
            title = cat['title']
            if(title in subcategories):
                points += 1.0
        score = points/len(pageCats)
        print_debug("Score of {w} is {s}".format(w=wiki_obj, s=str(score)))
        if(score >= self.sv):
            return True
        return False

    def randomPage(self, category, save, regen, check):
        """Generate a random page from a category.

        Input:
            Category (String): category to get page from
            Save (Boolean): whether or not to save subcategories to a file
            Regen (Boolean): whether or not to regenerate subcategory set
            Check (Boolean): whether or not to check page similarity
        Output:
            String: A random page belonging to category, or one of its subcats
        """
        subCats = []
        if(not regen):
            subCats = self.retreiveSubcategoriesFromLocation(category)
        if(regen or (not subCats)):
            print_debug("Rebuilding {category}".format(category=category))
            subCats = self.subcategoriesWithoutDuplicates(category)
        if(save or regen):
            self.saveArray(category, subCats)
        randomPage = None
        validRandomPage = True
        cat = random.sample(subCats, 1)[0]
        print_debug("Chose category {cat}".format(cat=cat))
        pages = self.wrappedRequest(cat, mode="Subpage")
        while(not randomPage or not validRandomPage):
            try:
                randomPage = random.choice(pages)
                title = randomPage['title']
                if(check):
                    print_debug("Checking " + title)
                    validRandomPage = self.checkSimilarity(title, subCats)
                    if(not validRandomPage):
                        pages.remove(randomPage)
            except IndexError as a:
                print_debug("{cat} has no pages. Retrying".format(cat=cat))
                subCats.remove(cat)
                if(len(subCats) == 0):
                    print_debug("No categories left. Sorry!")
                    raise ValueError("Category inputted is invalid.")
                cat = random.sample(subCats, 1)[0]
                print_debug("Chose category {cat}".format(cat=cat))
                pages = self.wrappedRequest(cat, mode="Subpage")
        return randomPage['title']


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
    print_debug(str(args.check))
    DEBUGGING = args.verbose
    max_depth = args.tree_depth
    similarityVal = args.similarity
    wb = WikiBot(max_depth, similarityVal)
    if(args.save):
        print_debug("Saving!")
    if(args.regen):
        print_debug("Regenerating!")

    print("https://en.wikipedia.org/wiki/" + wb.randomPage("Category:" +
                                                           args.category,
                                                           save=args.save,
                                                           regen=args.regen,
                                                           check=args.check
                                             )
    )
