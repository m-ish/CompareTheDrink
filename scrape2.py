# IMPORTS
# External
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from urllib.request import Request, urlopen
# Built-in
import concurrent.futures as threadingPool
import logging
from threading import Lock
# Custom
# from classItem import Item, ItemCollection

"""
The urls we will need to scrape to populate our database:
    bwsPopulateUrls = {'beer':'https://bws.com.au/beer/all-beer', 'wine':'https://bws.com.au/wine/all-wine', 'spirits':'https://bws.com.au/spirits/all-spirits'}

    liquorlandPopulateUrls = {'beer':'https://www.liquorland.com.au/beer', 'wine':'https://www.liquorland.com.au/search?q=wine', 'spirits':'https://www.liquorland.com.au/spirits'}

    danmurphysPopulateUrls = {'beer':'https://www.danmurphys.com.au/beer/all', 'wine':'https://www.danmurphys.com.au/list/wine', 'spirits':'https://www.danmurphys.com.au/spirits/all'}

    firstchoiceliquorPopulateUrls = {'beer':'https://www.firstchoiceliquor.com.au/beer', 'wine':'https://www.firstchoiceliquor.com.au/search?q=wine', 'spirits':'https://www.firstchoiceliquor.com.au/spirits'}

"""

def search(searchTerms):
    """
    The master function that handles the complete pipeline of going from a search url to returning a final list of drink items.

    Args:
        url: the url we are scraping from
    Returns:
        drinksData: A list of Items which the data for each drink
    """
    # These are the base search page urls that we will add our search terms to to search
    baseSearchUrls = list()
    baseSearchUrls.append("https://bws.com.au/search?searchTerm=")

    liquorlandSearchUrls = {'beer':'https://bws.com.au/beer/all-beer', 'wine':'https://bws.com.au/wine/all-wine', 'else':'https://www.liquorland.com.au/search?q='+searchTerms}
    miscSearchUrls = ["https://bws.com.au/search?searchTerm=", "", "https://www.danmurphys.com.au/search?searchTerm=", ]

    # Create a list of all the drinks data that we will scrape from all of the different liquor stores
    allDrinksData = list()

    # Get the search urls for each of the liquor sites for these search terms
    for baseSearchUrl in baseSearchUrls:
        # Add the search terms to the base search url to get the search url to scrape
        url = baseSearchUrl + searchTerms

        # 1 & 2. Scrape the html for the search page and create beautifulsoup (generic). Then get the url for each drink result in the search (specific)
        drinkUrls = getDrinks(url)

        if len(drinkUrls) == 0:
            print("NO DRINK RESULTS FOUND AT " + url + ".")
        else:
            # 3 & 4. Follow each of the drink links utilising multiple threads to speed the process. Inside of each thread, once again scrape the page to a spoup (general), then get all the drink data from the drink page (specific)
            allDrinksData.extend(getDrinksData(drinkUrls))

    # Sort the drinks by efficiency descending
    if len(allDrinksData) == 0:
        print("NO DRINK RESULTS FOUND ACROSS ANY SUPPORTED SITES.")
    else:
        allDrinksData = sortByEfficiency(allDrinksData)

    # Return the data for all of the drinks found across the liquor sites
    return allDrinksData

def download(url):
    """
    Function to parse a site and return a BeautifulSoup of its HTML

    Args:
        url: The url to be scraped
        target_filename: the output file that the data will be saved to
        filename_extension: file type of the output file
        total:
        list: a list for the output data to be put into

    Returns: A BeautifulSoup of the page html
    """
    # TODO: Possible implement ip proxy rotation to increase ban safety
    # We are now downloading the html from the given url
    print("DOWNLOADING AND RENDERING HTML FROM " + url + " ...")

    # Configure options for the chrome web driver which is used as a headless browser to scrape html and render javascript for web pages
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    # Get the HTML from the given url
    driver.get(url)
    # Create a BeautifulSoup object from the raw HTML string, to make it easier for us to search for particular elements later
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

def getSiteFromUrl(url):
    """
    Takes a search url (e.g. "https://bws.com.au/search?searchTerm="vodka") and automatically detects the site name and returns it
    """
    # Separate the url into list items about the periods
    urlList = url.split(".")
    # If the first element ends in www - e.g. url of form https://www.firstchoiceliquor.com.au/, take the second element in the list as the site name
    if urlList[0][-3:] == "www" or urlList[0][-3:] == "ww2":
        site = urlList[1]
    else:
        # If we have a url without a www. url e.g. urlList=["https://bws", "com", "au/search?searchTerm='vodka'"] simply take the first element, split by the '/' and take the element in posiiton 2 of the resulting list
        site = urlList[0].split("/")[2]
    return site

def getDrinks(url):
    """
    A function to find the link to every drink result to a liquor site search.
    """
    # Create a new soup all results which holds a list of html soups of each of the results pages
    allPageSoups = list()

    # Detect the liquor site we are scraping from the url. This allows to extract the drinks using the correct strategies for the specific website.
    site = getSiteFromUrl(url)


    # Get a list of the html soups of all of the search pages
    if site == "bws":
        allPageSoups.extend(getAllSearchPagesBws(url))

    elif site == "liquorland":
        print("Sorry, LiquorLand is not currently a supported site.")


    # Get the drinks profiles based on what site is being scraped
    if site == "bws":
        drinkUrls = getDrinksBws(allPageSoups)
    elif site == "liquorland":
        # print("Yeet!")
        # print(soup.prettify())
        # # Extract the drink profiles from the soup
        # specials = soup.findAll('div', {'class':'product-tile-wrapper update-specials-border'})
        # drinks = soup.findAll('div', {'class': 'product-tile-wrapper'})
        # drinks.append(specials)
        print("Sorry, LiquorLand is not currently a supported site.")
    elif site == "danmurphys":
        print("Sorry, Dan Murphy's is not currently a supported site.")
        # TODO: Implement drink url extraction from dan murphys search page
    elif site == "firstchoiceliquor":
        print("Sorry, First Choice Liquor is not currently a supported site.")
        # TODO: Implement drink url extraction from first choice liquor search page

    # Print out how many drink urls were found on the page
    print("FOUND " + str(len(drinkUrls)) + " DRINK URLS ON PAGE.")
    # Return the list of drink urls for us to individually scrape later on
    return drinkUrls

def getDrinksData(drinkUrls):
    """
    Function to get a list of drink data from a BeautifulSoup and return the data in a list

    Args:
        drinkUrls: a list of urls to the individual pages of the drinks found

    Returns: A list of drink data
    """
    # Now, the drink data must be extracted for each drink url found
    print('NOW EXTRACTING DRINKS DATA FROM DRINK URLS ...')

    # Create an empty list in which to store our drinks data (each drink will have its own Item object (see classItem) which will be added to the list)
    commonList = list()

    # Detect the liquor site we are scraping from the url. This allows to extract the drink data using the correct strategies for the specific website.
    site = getSiteFromUrl(drinkUrls[0])

    # Get the data from the drink url pages using the functions for the current liquor site
    if len(drinkUrls) == 0:
        # If there were no drinkUrls given, don't attempt to get data
        return commonList
    else:
        # If there are drinkUrls, however, get the data from them
        threads = 0
        _lock = Lock()
        with threadingPool.ThreadPoolExecutor(max_workers=1) as executor:
            # Note: Threading stuff basically executes multiple copies getDrinksDataXXX(url, commonList, _lock) concurrently
            for url in drinkUrls:
                # Print out every time a new thread is initialised
                print("INITIALISING THREAD " + str(threads) + ".")

                # Extract the drink data based on the site being scraped
                if site == "bws":
                    # Retrieve drink data from bws format html
                    executor.submit(getDrinksDataBws, url, commonList, _lock)
                elif site == "liquorland":
                    print("SORRY, DRINK DATA EXTRACTION IS NOT YET IMPLEMENTED FOR LIQUORLAND.")
                    # # Run item_thread_liquorland(item)
                    # executor.submit(item_thread_liquorland, item, drinksdata, _lock)
            # Update how many threads we have initialised
            threads += 1

    # Return the drinksData
    return commonList

def sortByEfficiency(drinksData):
    """
    A function to sort a list of drinksData by descending efficiency
    """
    # Print our current status
    print("SORTING THE DRINKS DATA BY EFFICIENCY (DSC) ...")
    # Sort the list of drinksData by descending efficiency
    drinksData.sort(key = sortEighth, reverse = True)
    # Return the drinks data
    return drinksData

def sortEighth(val):
    """
    Function to return the eighth element of the two elements passed as the parameter
    """
    return val[8]

"""________________________________________SPECIFIC FUNCTIONS____________________________________________"""

def getAllSearchPagesBws(url):
    """
    A function to get the html soups of all the results pages for a search, given the url for the first page of results.
    If we are on bws, the results are stored on multiple pages, loaded one at a time, so we will check each page to see if there is a "show more results" button and if there is we will go the ne next results page (page number is determined by the page url)

    Args:
        url: the url of the first page of search results
    Returns:
        allPageSoups: a list of the html soups of all the results pages
    """

    # Create a new soup all results which holds a list of html soups of each of the results pages
    allPageSoups = list()

    # Start scraping at results page one
    currentPage = 1
    # Print what page of results we are currently loading
    print("LOADING PAGE " + str(currentPage) + " OF RESULTS")        # Get the html for the current page of results
    currentPageSoup = download(url + "&pageNumber=" + str(currentPage))
    # Add current page soup to list
    allPageSoups.append(currentPageSoup)
    # Get the html element for the "load more" button
    loadMoreButtonDiv = currentPageSoup.find('div', {'class':'progressive-paging-bar--container'})
    loadMoreButton = loadMoreButtonDiv.find('a', {'class':'btn btn-secondary btn--full-width ng-scope'})
    # While the hmtl for the "load more" button is not null there is a next page
    while loadMoreButton != None:
        # Increment the number of the current page
        currentPage = currentPage + 1
        # Print what page of results we are currently loading
        print("LOADING PAGE " + str(currentPage) + " OF RESULTS")
        # Get the html for the current page of results
        currentPageSoup = download(url + "&pageNumber=" + str(currentPage))
        # Add current page soup to list
        allPageSoups.append(currentPageSoup)
        # Get the html element for the "load more" button
        loadMoreButtonDiv = currentPageSoup.find('div', {'class':'progressive-paging-bar--container'})
        loadMoreButton = loadMoreButtonDiv.find('a', {'class':'btn btn-secondary btn--full-width ng-scope'})

    # Return the list containing all of html soup for every search page
    return allPageSoups


def getDrinksBws(soups):
    """
    Drink url extraction for bws

    Args:
        soup: a html soup of a liquor site search page
    Returns:
        drinkUrls: a list of urls for specific drink pages
    """
    # Create a new list to store the urls to each of the drinks
    drinkUrls = list()
    # For each page of results, scrape all of the drink urls off of the page
    for soup in soups:
        # Create a new list to store the drinks
        drinks = list()
        # Extract the drink cards from the search page soup
        drinksList = soup.find('div', {'class':'center-panel-ui-view ng-scope'})
        drinks = drinksList.findAll('div', {'class':'productTile'})
        for drink in drinks:
            # Extract the urls to each individual drink page
            relativePath = drink.find('a', {'class':'link--no-decoration'})['href']
            drinkUrls.append("https://bws.com.au" + relativePath)
    # Return the list containing the urls to each drink on each results page
    return drinkUrls

def getDrinksDataBws(url, commonList, _lock):
    """
    Thread function to control parsing of BWS drink details

    Args:
        url: the url of the website for the specific drink product we are collecting the data for
        commonList: the list of drink data that all threads store their results in
        _lock: some threading shit (ask Hamish I guess)

    Returns:
        none (simply adds the result to the common list, since this function is running within a multi-threaded environment)
    """
    # Print our current status
    print("GETTING DRINK DATA FROM A DRINK PAGE ...")

    # Get the html soup for the drink page
    soup = download(url)

    # Extract the name
    name = soup.find('div', {'class':'detail-item_title'}).text

    # Extract the price
    priceElement = soup.find('span', {'class': 'trolley-controls_volume_price'})
    dollar = priceElement.find('span', {'class': 'ng-binding'}).text
    cents = priceElement.find('sup', {'class': 'ng-binding'}).text
    price = str(dollar) + '.' + str(cents)

    # Extract the product image link (the src attribute of the image)
    image = soup.find('img', {'class': 'product-image'})['src']

    # Get the footer element containing all the rest of the details
    detailsRaw = soup.find('div', {'class':'product-additional-details_container text-center ng-isolate-scope'})
    # Get the ul of details inside the element
    list = detailsRaw.find('ul', {'class':'text-left'})
    # TODO: Remove this debug statement
    # Get all the titles of the properties
    keys = list.findAll('strong', {'class':'list-details_header ng-binding'})
    # Get all the values of the proverties
    values = list.findAll('span', {'class':'pull-right list-details_info ng-binding ng-scope'})
    # Put the titles and values as K,V pairs into a dictionary
    details = dict()
    for x in range(0, len(keys)):
        details[keys[x].text] = values[x].text

    # Extract the product brand
    brand = details['Brand']

    # Extract the bottle volume
    size = 0
    if details['Liquor Size'].find('mL') != -1:
        # measurement in mL
        strSize = details['Liquor Size'][0:len(details['Liquor Size']) - 2]
        size = int(strSize) / 1000
    else:
        # measurement in L
        strSize = details['Liquor Size'][0:len(details['Liquor Size']) - 1]
        size = int(strSize)

    # Find the price per standard by getting the number of standard drinks and dividing it by the price
    efficiency = float(details['Standard Drinks']) / float(price)

    # Put all of the details found for the drink into an Item object
    # entry = Item("BWS", brand.text, name.text, price, "https://bws.com.au" + link['href'], details['Liquor Size'], details['Alcohol %'], details['Standard Drinks'], efficiency)
    entry = ["BWS", details['Brand'], name, price, url, size, details['Alcohol %'], details['Standard Drinks'], efficiency, image]

    # Print out the list of drink data
    print("GOT DRINK DATA FOR: " + str(entry))

    # Add the list of data for this drink to the list of drinksData
    commonList.append(entry)

    # Handle the closing of the thread
    _lock.acquire()
    _lock.release()


"""________________________________________DEBUG MAIN FUNCTION____________________________________________"""
#
# def main():
#     # Get the initial query
#     query = input("Please enter term to search for: ")
#     # while query !== "q":
#     print("START DEBUG SCRIPT")
#     commonList = scrape("https://bws.com.au/search?searchTerm=" + query)
#     print("")
#     print("")
#     print("SCRAPE RESULTS: ")
#     for item in commonList:
#         print(str(item))
#     print("")
#         # query = input("Please enter term to search for (or enter 'q' to quit): ")
#     print("END DEBUG SCRIPT")
#
# main()
