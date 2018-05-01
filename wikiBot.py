import requests
import random
import argparse
import sys
from pyquery import PyQuery
DEBUGGING = False
max_depth = 4
current_depth = 0
header = "Garrett Credi's Random Page Bot(Contact @ gcc@ameritech.net)"
headerVal = {'Api-User-Agent': header}
def print_debug(str):
    global DEBUGGING
    if(DEBUGGING):
        print("DEBUG: " + str)

def subcatUrlGen(category):
    return "https://en.wikipedia.org/w/api.php?format=json&action=query&list=categorymembers&cmtitle=" + category + "&cmlimit=500&cmtype=subcat"

def subpageUrlGen(category):
    return "https://en.wikipedia.org/w/api.php?format=json&action=query&list=categorymembers&cmtitle=" + category + "&cmlimit=500&cmtype=page"
def subCatRequest(category):
    global DEBUGGING, headerVal
    max_times = 5
    times = 0
    while(times<max_times):
        try:
            r = requests.get(subcatUrlGen(category), headers=headerVal)
            return r.json()['query']['categorymembers']
        except requests.exceptions.ConnectionError as e:
            if(times>max_times):
                print_debug(category + " failed too many times (" + str(times) + ") times. Moving on")
                times = 0
                return [category]
            else:
                print_debug("Retrying " + category + " due to connection error")
                times += 1
def subpageRequest(category):
    try:
        r = requests.get(subpageUrlGen(category), headers=headerVal)
        results = r.json()
        return results['query']['categorymembers']
    except requests.exceptions.ConnectionError as e:
        if(times>max_times):
            print_debug(category + " failed too many times (" + str(times) + ") times. Moving on")
            times = 0
            return [category]
        else:
            print_debug("Retrying " + category + " due to connection error")
            times += 1

def getSubcategories(category):
    global max_depth, DEBUGGING
    current_depth = 1
    singleStepSubcategories = [category]
    allSubcategories = []
    while(current_depth<=max_depth):
        print_debug("Current tree depth " + str(current_depth))
        subcategoryTemp = []
        if(len(singleStepSubcategories)==0):
            break
        for subcat in singleStepSubcategories:
            allSubcategories.append(subcat)
            subcategories = subCatRequest(subcat)
            if(len(subcategories)!=0):
                subCatsExist = True
            for cat in subcategories:
                title = cat['title']
                print_debug(subcat + " has subcategory " + title)
                if(title not in allSubcategories):
                    allSubcategories.append(title)
                    subcategoryTemp.append(title)
                else:
                    print_debug(title + " already checked. Moving on")
        singleStepSubcategories = subcategoryTemp
        current_depth += 1
    return allSubcategories



def saveArray(category,subcats):
    filename = category+"_subcats.txt"
    print_debug("Saving to " + filename)
    with open(filename, 'w') as f:
        for cat in subcats:
            f.write(cat+"\n")

def randomPage(category, save=False, regen = False):
    global DEBUGGING
    subCats = []
    if(not regen):
        try:
            subCatFile = open(category+"_subcats.txt", 'r')
            print_debug("Reading from " + category + "_subcats.txt")
            for count,line in enumerate(subCatFile):
                subCats.append(line)
            if(save):
                print_debug("Nevermind, not saving!")
            save = False
            subCatFile.close()
        except:
            print_debug(category + "_subcats.txt does not exist. Building from network")
            subCatsMaybeDup = getSubcategories(category)
            subCats = list(set(subCatsMaybeDup)) ##Weeds out duplicates
    else:
        print_debug("Rebuilding " + category)
        subCatsMaybeDup = getSubcategories(category)
        subCats = list(set(subCatsMaybeDup))
        save = True
    if(save):
        saveArray(category,subCats)
    randomSubcat = ""
    while(randomSubcat == ""):
        try:
            cat = random.choice(subCats)
            print_debug("Chose category " + cat)
            url = "https://en.wikipedia.org/w/api.php?format=json&action=query&list=categorymembers&cmtitle=" + cat + "&cmlimit=500&cmtype=page"
            r = requests.get(url, headers=headerVal)
            results = r.json()
            pages = results['query']['categorymembers']
            randomSubcat = random.choice(pages)['title']
        except IndexError as a:
            print_debug(cat + " has no pages. Retrying")
    return randomSubcat
if(__name__=="__main__"):
    parser = argparse.ArgumentParser(description='Get a random page from a wikipedia category.')
    parser.add_argument('category', help="The category you wish to get a random page from.")
    parser.add_argument('--tree_depth', nargs='?', type=int, default=4, help="How far down to traverse the subcategory tree")
    parser.add_argument("-s", "--save", action="store_true", help="Save subcategories to a file for quick re-runs")
    parser.add_argument("-r", "--regen", action="store_true", help="Regenerate the subcategory file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug lines")
    args = parser.parse_args()
    DEBUGGING = args.verbose
    max_depth = args.tree_depth
    if(args.save and DEBUGGING):
        print("Saving!")
    if(args.regen and DEBUGGING):
        print("Regenerating!")
    print("https://en.wikipedia.org/wiki/" + randomPage("Category:"+args.category, save=args.save, regen=args.regen))
