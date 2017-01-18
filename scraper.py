import codecs
import os.path
import time

import requests
from bs4 import BeautifulSoup as bs
import scraperwiki


BASE_URL = 'http://www.cqc.org.uk'
def fetch_all():
    page = 0
    stop = False
    while not stop:
        print('page: {}'.format(page))
        tmpl = 'http://www.cqc.org.uk/search/services/care-homes?page={}&sort=default&mode=html&f[0]=bundle%3Alocation&f[1]=im_field_more_services%3A3667'
        try:
            r = requests.get(tmpl.format(page))
            time.sleep(0.5)
        except:
            print('hmm.. Failed to fetch page {}'.format(page))
            time.sleep(2)
            continue
        if r.status_code != 200:
            print('hmm.. Failed to fetch page {}'.format(page))
            time.sleep(2)
            continue
        soup = bs(r.text, 'html.parser')
        results = soup.find_all(class_='result-item')
        if len(results) == 0:
            break
        for result_soup in results:
            parse_result(result_soup)
        page += 1

def parse_result(result):
    obj = {
        'awaiting_inspection': False,
        'archived_date': None,
        'action_taken': False,
        'new_url': None,
        'old_url': None,
    }
    rel_url = result.a['href']
    obj['id_'] = rel_url.split('/')[-1]
    obj['url'] = BASE_URL + rel_url
    heading = [x.strip() for x in result.find(class_='facility-name').strings]
    obj['name'] = heading[0]
    obj['rating'] = heading[1] if len(heading) > 1 else None
    details_soup = result.find(class_='details')
    details = [x.strip() for x in details_soup.strings]
    obj['address'] = details[1]
    obj['postcode'] = obj['address'].split(',')[-1].strip()
    if details[2] == 'Provided by:':
        obj['phone'] = None
        obj['provider_name'] = details[3]
    else:
        obj['phone'] = details[2]
        obj['provider_name'] = details[4]
    obj['provider_url'] = BASE_URL + details_soup.a['href']
    warning_soups = result.find(class_='warning-messages')
    warning_soups = warning_soups.find_all('div') if warning_soups else []
    for warning_soup in warning_soups:
        class_ = warning_soup.get('class')[0]
        if class_ == 'archived-message':
            obj['archived_date'] = [a for a in warning_soup.strings][0][12:-2]
        elif class_ == 'relationship-header':
            if warning_soup.a.text == 'see new profile':
                obj['new_url'] = BASE_URL + warning_soup.a['href']
            elif warning_soup.a.text == 'see old profile':
                obj['old_url'] = BASE_URL + warning_soup.a['href']
            else:
                print('unknown warning:')
                print(warning_soup)
        elif class_ == 'urt-message':
            obj['awaiting_inspection'] = True
        elif class_ == 'warning-message':
            obj['action_taken'] = True
        else:
            print('unknown warning:')
            print(warning_soup)
    scraperwiki.sqlite.save(unique_keys=['id_'], data=obj)

fetch_all()
