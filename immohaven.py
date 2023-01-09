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

def get_data():
    result = []
    resp = requests.get('https://www.immohaven.be/nl/te-huur')

    soup = BeautifulSoup(resp.content)

    link = 'https://www.immohaven.be/nl/te-huur?view=list&task=showAjaxList&page='

    address = soup.find('div',class_='contact_details').find('div',class_='contact_address').text

    contact = soup.find('div',class_='contact_details').find('div',class_='contact_details_telephone').text

    email = soup.find('div',class_='contact_details').find('div',class_='contact_details_emailto').text

    i = 1
    while True:
        url = link+str(i)
        resp1 = requests.get(url)
        data = resp1.json()
        if not data['list']['Items']:
            break

        for dd in data['list']['Items']:
            external_link = 'https://www.immohaven.be/nl/te-huur?view=detail&id='+str(dd['ID'])
            external_source = 'Immo HavenSpider'
            title = dd['MainTypeName']+' TE '+dd['City']+'('+dd['Zip']+')'
            description = dd['DescriptionA']
            room_count = dd['NumberOfBedRooms']
            rent = dd['Price']

            img_resp = requests.get(external_link)
            img_soup = BeautifulSoup(img_resp.content)

            imgs = set()
            if img_soup.find('div',class_='picswiper'):
                for im in img_soup.find('div',class_='picswiper').find_all('img'):
                    imgs.add(im['src'])
            else:
                imgs = set()
            images = list(imgs)
            external_images_count = len(images)

            city = dd['City']
            lattitude = dd['GoogleX']
            longitude = dd['GoogleY']
            zipcode = dd['Zip'] 

            property_type = dd['WebIDName']

            l = {}
            if 'lift'  in dd['DescriptionA'] or 'elevator' in dd['DescriptionA']:
                l.update({'elevator':True})
            else:
                l.update({'elevator':False})
            if 'swimming' in dd['DescriptionA']:
                l.update({'swimming_pool':True})
            else:
                l.update({'swimming_pool':False})
            if 'furnish' in dd['DescriptionA']:
                l.update({'furnished':True})
            else:
                l.update({'furnished':False})
            if 'balcony' in dd['DescriptionA']:
                l.update({'balcony':True})
            else:
                l.update({'balcony':False})
            if 'terrace' in dd['DescriptionA']:
                l.update({'terrace':True})
            else:
                l.update({'terrace':False})
            if 'parking' in dd['DescriptionA']:
                l.update({'parking':True})
            else:
                l.update({'parking':False})
            l['external_link'] = external_link
            l['external_source'] = external_source
            l['title'] = title
            l['description'] = description
            l['room_count'] = room_count
            l['rent'] = rent
            l['images'] = images
            l['external_images_count'] = external_images_count
            l['city'] = city
            l['lattitude'] = lattitude
            l['longitude'] = longitude
            l['zipcode'] = zipcode
            l['property_type'] = property_type
            l['landlord_phone'] = contact
            l['landlord_email'] = email
            l['landlord_address'] = address


            add = ''
            if img_soup.find('div',class_='span4 panel-left'):
                for div in img_soup.find('div',class_='span4 panel-left').find_all('div',class_='field'):
                    if 'Adres' in div.text:
                        add = div.text.strip().replace('\n',' ').replace('Adres : ','')
            else:
                add = ''
            l['address'] = add
            result.append(l)
        i = i+1
    return result

def write_json():
    data = get_data()
    data = json.dumps(data)
    with open('immohaven.json','w') as f:
        f.write(data)
write_json()
