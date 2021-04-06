#################################
##### Name: Soyoung Lee
##### Uniqname: soyolee
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time


BASEURL = 'https://www.nps.gov'
CACHE_FILE_NAME = 'cache_nationalsite_scrapels.json'

def open_cache():
    ''' opens the cache file if it exists and loads the JSON into
    a dictionary, which it then returns.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''

    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILE_NAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.

    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''

    def __init__(self, category, name, address, zipcode, phone):
        '''Initialize a NationalSite instance.'''

        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        '''String representation of the object.'''

        return f'{self.name} ({self.category}): {self.address} {self.zipcode}'

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    state_url_dict = {}
    response = requests.get(BASEURL)
    soup = BeautifulSoup(response.text, 'html.parser')
    state_list = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    state_url_list = state_list.find_all('a', href=True)
    for state_url in state_url_list:
        state_url_dict[state_url.text.lower()] = BASEURL + state_url['href']
    save_cache(state_url_dict)
    return state_url_dict


def get_site_instance(site_url, cache):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    cache: dictionary
        The cache dictionary

    Returns
    -------
    instance
        a national site instance
    '''
    if (site_url in cache.keys()): # michigan total # site_url = park_site_url
        response_site_detail = cache[site_url]
        print('Using cache')
    else:
        response_sit_detail = requests.get(site_url) # go to each site
        cache[site_url] = response_sit_detail.text
        print('Fetching')
        save_cache(cache)
        response_site_detail = cache[site_url]

    soup_site = BeautifulSoup(response_site_detail, 'html.parser')

    park_detail_1 = soup_site.find('div', class_='Hero-titleContainer clearfix')
    # name
    park_name = soup_site.find('a', class_='Hero-title').text
    # type
    park_type = soup_site.find('span', class_='Hero-designation').text
    # address(city, state), zip code
    park_detail_2 = soup_site.find('p', class_='adr')
    park_address_city = park_detail_2.find('span', itemprop='addressLocality').text
    park_address_state = park_detail_2.find('span', itemprop='addressRegion').text
    park_address = park_address_city + ', ' + park_address_state
    # zip code
    park_zip = park_detail_2.find('span', itemprop='postalCode').text
    # phone
    park_detail_3 = soup_site.find('div', class_='vcard')
    park_phone = park_detail_3.find('span', itemprop='telephone').text.strip()
    # call the class to initiate an instance
    park_instance = NationalSite(park_type, park_name, park_address, park_zip, park_phone)
    return park_instance

def get_sites_for_state(state_url, cache):
    '''Make a list of national site instances from a state URL.

    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov

    cache: dictionary
        The cache dictionary

    Returns
    -------
    list
        a list of national site instances
    '''

    national_sites_for_state_instance_list = []

    if (state_url in cache.keys()): # michigan total
        response_state_park_list = cache[state_url]
    else:
        response_state_park_list = requests.get(state_url) # michigan total
        cache[state_url] = response_state_park_list.text
        save_cache(cache)
        response_state_park_list = cache[state_url]

    soup_site_url = BeautifulSoup(response_state_park_list, 'html.parser')

    #print(soup_site_url)
    park_list = soup_site_url.find('ul', id='list_parks')
    park_list_h3 = park_list.find_all('h3')

    # park list by state
    for park_url in park_list_h3:
        park_url_a = park_url.a
        park_site_url = BASEURL + park_url_a['href'] # get each site url
        site_instance = get_site_instance(park_site_url, cache)
        national_sites_for_state_instance_list.append(site_instance)

    return national_sites_for_state_instance_list

def main_interaction():
    '''Create an interactive search :
    Ask a user to enter a state name and provide a list of national sites in the state.
    If a user enters 'exit', end the program. If a user enters an invalid name, print an error 
    and ask the user to input again.
    After the list is successfully printed, ask the user to enter the nubmer to get more info.

    Parameters
    ----------
    None

    Returns
    -------
    None

    '''

    user_input = input("Enter a state name(e.g. Michigan, michigan) or 'exit' to quit. ")

    if user_input.lower() == 'exit':
        quit()
    else:
        try :
            if user_input.lower() in cache.keys():
                state_url = cache[user_input.lower()] # all sites in the state
            else:
                state_url_list = build_state_url_dict() # all sites in the state
                state_url = state_url_list[user_input.lower()]

            result = get_sites_for_state(state_url, cache)
            print('-'*40)
            print(f'List of national sites in {user_input}')
            print('-'*40)
            for number, lst in enumerate(result, start=1):
                print(f'[{number}] {lst.info()}')
        except:
            print("[Error] Please enter a proper state name.")
            main_interaction()
        detail_info(result)


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    BASEURL_MAP = 'http://www.mapquestapi.com/search/v2/radius'
    API_KEY = secrets.MAP_API_KEY
    origin = site_object.zipcode
    radious = 10
    maxMatches = 10
    outFormat = 'json'

    map_search_URL = f'{BASEURL_MAP}?key={API_KEY}&origin={origin}&radious={radious}&maxMatches={maxMatches}&outFormat={outFormat}&ambiguities=ignore'

    if (map_search_URL in cache.keys()):
        map_search_results = cache[map_search_URL]
        print('Using Cache')
    else:
        map_search_results = requests.get(map_search_URL).json()
        cache[map_search_URL] = map_search_results
        print('Fetching')
        save_cache(cache)
        map_search_results = cache[map_search_URL]

        print('-'*40)
        print(f'Place near {site_object.name}')
        print('-'*40)

    for map_search_result in map_search_results['searchResults']:
        if map_search_result['name']:
            map_search_result_name = map_search_result['name']
        else:
            map_search_result_name = 'no name'
        if map_search_result['fields']['group_sic_code_name_ext']:
            map_search_result_category = map_search_result['fields']['group_sic_code_name_ext']
        else:
            map_search_result_category = 'no category'
        if map_search_result['fields']['address']:
            map_search_result_address = map_search_result['fields']['address']
        else:
            map_search_result_address = 'no address'
        if map_search_result['fields']['city']:
            map_search_result_city = map_search_result['fields']['city']
        else:
            map_search_result_city = 'no city'
        print(f'- {map_search_result_name} ({map_search_result_category}): {map_search_result_address}, {map_search_result_city}')

def detail_info(instance_list):
    '''Provide API data from MapQuest API of the number a user entered.

    Parameters
    ----------
    instance_list: instance
        a list of instances of the national site result

    Returns
    -------
    None
    '''
    user_input_detail = input("Choose the number for detail search or 'exit' or 'back' ")
    if user_input_detail.lower() == 'exit':
        quit()
    elif user_input_detail.lower() == 'back':
        main_interaction()
    else:
        try :
            site_object = instance_list[int(user_input_detail) - 1]
            get_nearby_places(site_object)
        except:
            print("[Error] Please enter valid number or text.")
    detail_info(instance_list)

if __name__ == "__main__":

    cache = open_cache()
    main_interaction()