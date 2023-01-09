import requests
from bs4 import BeautifulSoup
import re,json
import geopy
from geopy.geocoders import Nominatim
# from geopy.extra.rate_limiter import RateLimiter
geolocator = Nominatim()

def clean_value(text):
    if text is None:
        text = ""
    if isinstance(text,(int,float)):
        text = str(text.encode('utf-8').decode('ascii', 'ignore'))
    text = str(text.encode('utf-8').decode('ascii', 'ignore'))
    text = text.replace('\t','').replace('\r','').replace('\n','')
    return text.strip()

def clean_key(text):
    if isinstance(text,str):
        text = ''.join([i if ord(i) < 128 else ' ' for i in text])
        text = text.lower()
        text = ''.join([c if 97 <= ord(c) <= 122 or 48 <= ord(c) <= 57 else '_'                                                                                         for c in text ])
        text = re.sub(r'_{1,}', '_', text)
        text = text.strip("_")
        text = text.strip()

        if not text:
            raise Exception("make_key :: Blank Key after Cleaning")

        return text.lower()
    else:
        raise Exception("make_key :: Found invalid type, required str or unicode                                                                                        ")

def traverse( data):
    if isinstance(data, dict):
        n = {}
        for k, v in data.items():
            k = str(k)
            if k.startswith("dflag") or k.startswith("kflag"):
                if k.startswith("dflag_dev") == False:
                    n[k] = v
                    continue

            n[clean_key(clean_value(k))] = traverse(v)

        return n

    elif isinstance(data, list) or isinstance(data, tuple) or isinstance(data, set):                                                                                     
        data = list(data)
        for i, v in enumerate(data):
            data[i] = traverse(v)

        return data
    elif data is None:
        return ""
    else:
        data = clean_value(data)
        return data

def get_records(soup):
    result = []
    for di in soup.find('div',class_='row ev-search-results').find_all('div',recursive=False):
        rec = {}
        if not di.find('a',class_='ev-property-container'):
            continue
        if not di.find('div',class_='ev-teaser-title'):
            continue
        external_link = di.find('a',class_='ev-property-container')['href']
        title = di.find('div',class_='ev-teaser-title').text
        print external_link,title
        address = di.find('div',class_='ev-teaser-subtitle').text
        external_source = 'ENGEL & VOLKERS SABLON SPider'
        landlord_name = 'ENGEL & VOLKERS SABLON'
        room_count = 0
        if di.find('img',title='Bedrooms'):
            room_count = di.find('img',title='Bedrooms').find_next('span').text
        else:
            room_count = 0
        rent = di.find('div',class_='ev-teaser-price').find('div',class_='ev-value').text
        city = address.split(',')[-1].strip().replace('city','').replace(')','').replace('(','')
        rec['title']= title
        rec['address']= address
        rec['external_source']= external_source
        rec['landlord_name']= landlord_name
        rec['external_link']= external_link
        rec['room_count']= room_count
        rec['rent']= rent
        rec['city']= city
        ss= None
        try:
            ss = geolocator(city)
        except:
            pass
        resp1 = requests.get(external_link)
        soup1 = BeautifulSoup(resp1.content)
        if ss:
            rec['latitude'] = ss.latitude
            rec['longitude'] = ss.longitude
        else:
            rec['latitude'] = None
            rec['longitude'] = None   


        desc1= soup1.find_all('h2')[1].find_next('ul').text

        desc2 = soup1.find_all('h2')[2].find_next('ul').text

        desc = soup1.find('p',itemprop='description').text

        description = desc1+' '+desc2+' '+desc
        rec['description'] = description

        if 'lift' in description.lower() or 'elevator' in description.lower():
            rec.update({'elevator':True})
        else:
            rec.update({'elevator':False})
        if 'swimming' in description.lower():
            rec.update({'swimming_pool':True})
        else:
            rec.update({'swimming_pool':False})
        if 'furnish' in description.lower():
            rec.update({'furnished':True})
        else:
            rec.update({'furnished':False})
        if 'balcony' in description.lower():
            rec.update({'balcony':True})
        else:
            rec.update({'balcony':False})
        if 'terrace' in description.lower():
            rec.update({'terrace':True})
        else:
            rec.update({'terrace':False})
        if 'parking' in description.lower():
            rec.update({'parking':True})
        else:
            rec.update({'parking':False})
        rec['zipcode'] = None
        rec['property_type'] = soup1.find('div',class_='ev-exposee-content ev-exposee-subtitle').text.split(',')[0].strip()
        rec['landlord_email'] = ''
        rec['landlord_phone']=soup1.find('li',itemprop='contactPoint').text.replace('Phone:','').strip()
        rec['landlord_address']=soup1.find('li',itemprop='address').text.strip()
        images = []
        for im in soup1.find('div',class_='ev-image-gallery-frame').find_all('img'):
            images.append(im['src'])
        rec['images'] = images
        rec['external_images_count'] = len(images)
        result.append(rec)
    return result

def get_data():
    resp = requests.get('https://www.engelvoelkers.com/en/search/?q=&startIndex=0&businessArea=residential&sortOrder=DESC&sortField=sortPrice&pageSize=18&facets=bsnssr%3Aresidential%3Bcntry%3Abelgium%3Brgn%3Abrussels_surroundings%3Btyp%3Arent%3B')

    soup = BeautifulSoup(resp.content)
    
    res = get_records(soup)
    while True:
        if not soup.find('ul',class_='ev-pager-row').find('a',class_='ev-pager-next'):
            break
        nex = soup.find('ul',class_='ev-pager-row').find('a',class_='ev-pager-next')['href']
        print nex
        resp = requests.get(nex)
        soup = BeautifulSoup(resp.content)
        res.extend(get_records(soup))
    return res

def write_json():
    data = get_data()
    data = json.dumps(data)
    with open('engel.json','w') as f:
        f.write(data)
write_json()