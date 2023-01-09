import requests
from bs4 import BeautifulSoup
import re,json
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

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

def get_rec():
    resp = requests.get('https://www.defactovastgoed.be/')

    soup = BeautifulSoup(resp.content)

    jj = []
    for city in soup.find('select',attrs={'name':'cities'}).find_all('option'):
        jj.append(('cities',city['value']))

    jj.append(('price-from',''))

    jj.append(('price-to',''))

    resp1 = requests.get('https://www.defactovastgoed.be/aanbod?',params=jj)

    soup1 = BeautifulSoup(resp1.content)

    divs = soup1.find_all('div',class_='pand-wrapper')

    records = get_records(divs)
    links = []
    for a in soup1.find('div',class_='paging-numbers').find_all('a'):
        link = 'https://www.defactovastgoed.be/'+a['href']
        links.append(link)

    for li in links:
        resp1 = requests.get(li)
        soup1 = BeautifulSoup(resp1.content)
        divs = soup1.find_all('div',class_='pand-wrapper')
        records.extend(get_records(divs))
    return records

def get_records(divs):
    ll = []
    for div in divs:
        reco = {}
        city = div.find('h2').text.strip()
        external_link = 'https://www.defactovastgoed.be/'+div.find('h2').find('a')['href']
        external_source = 'Bedrijfvastgoed De Facto Spider'
        property_type = div.find('li').text.strip().replace('Type: ','')
        outer_desc = div.find('h3').text.strip()+' '+div.find('h3').find_next('p').text.strip()
        reco['city'] = city
        reco['external_link'] = external_link
        reco['external_source'] = external_source
        reco['property_type'] = property_type
        reco['outer_desc'] =outer_desc 
        ll.append(reco)
    return ll

def get_data():
    result = []
    for l in get_rec():

        resp = requests.get(l['external_link'])
        soup = BeautifulSoup(resp.content)

        record = {}
        for script in soup.find_all('script'):
        #     if 'google.map' in (script):
            if (script.contents) and 'google.maps' in script.contents[0]:
                if (re.findall('google.maps.LatLng\((.*?)\)',script.contents[0])[0]):
                    record.update({'latitude':re.findall('google.maps.LatLng\((.*?)\)',script.contents[0])[0].split(',')[0]})
                    record.update({'longitutde':re.findall('google.maps.LatLng\((.*?)\)',script.contents[0])[0].split(',')[1]})
                else:
                    record.update({'latitude':None})
                    record.update({'longitutde':None})
            else:
                record.update({'latitude':None})
                record.update({'longitutde':None})
        l.update(record)

        imgs = []
        for pic in soup.find_all('picture'):
            imgs.append(pic.find('img')['src'])
        l['images'] = imgs
        l["external_images_count"] = len(imgs)


        if 'lift' in soup.find('div',class_='container main-content').text.lower() or 'elevator' in soup.find('div',class_='container main-content').text.lower():
            l.update({'elevator':True})
        else:
            l.update({'elevator':False})
        if 'swimming' in soup.find('div',class_='container main-content').text.lower():
            l.update({'swimming_pool':True})
        else:
            l.update({'swimming_pool':False})
        if 'furnish' in soup.find('div',class_='container main-content').text.lower():
            l.update({'furnished':True})
        else:
            l.update({'furnished':False})
        if 'balcony' in soup.find('div',class_='container main-content').text.lower():
            l.update({'balcony':True})
        else:
            l.update({'balcony':False})
        if 'terrace' in soup.find('div',class_='container main-content').text.lower():
            l.update({'terrace':True})
        else:
            l.update({'terrace':False})
        if 'parkee' in soup.find('div',class_='container main-content').text.lower():
            l.update({'parking':True})
        else:
            l.update({'parking':False})


        l['landlord_name'] = 'De Facto Bedrijfvastgoed'


        l['description'] = clean_value(soup.find('div',class_='container main-content').text.lower().strip())

        l['landlord_email'] = soup.find('address').find('a').text

        l['landlord_phone'] = soup.find('address').text.split('\r\n')[1]

        l['address'] = clean_value(soup.find('address').text.strip().replace(l['landlord_email'],'').replace(l['landlord_phone'],'').strip())
        l['zipcode'] = ''
        result.append(l)
    return result

def write_json():
    data = get_data()
    data = json.dumps(data)
    with open('defacto.json','w') as f:
        f.write(data)

write_json()
