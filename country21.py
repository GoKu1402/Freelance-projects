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
    resp = requests.get('http://www.century21expo.be')

    soup = BeautifulSoup(resp.content)

    resp_cont = requests.get('https://www.century21.be/nl/kantoor/expo/kantoor/05316c84-bf47-4628-98ba-ebadfe14c019/contact')

    cont_soup = BeautifulSoup(resp_cont.content) 

    landlord_address = clean_value(cont_soup.find('address').text.strip())

    landlord_email = clean_value(cont_soup.find('span',attrs={'class':'icon icon-mail'}).find_next('span').text)

    landlord_phone = clean_value(cont_soup.find('span',attrs={'class':'icon icon-tel'}).find_next('span').text)

    param = {'transferType': 'RENT',
    'orderBy': 'updatedAt',
    'fullText': 'true',
    'start': '0',
    'nbResults': '30',}

    contact ={}

    contact['landlord_address'] = landlord_address
    contact['landlord_email'] = landlord_email
    contact['landlord_phone'] = landlord_phone

    resp1 = requests.get('https://api.century21.be/api/v1/agencies/0a2c850c-011b-462b-a81c-6a33e52ff805/properties?',params=param)

    properties = resp1.json()['properties']

    result = []
    for proper in properties:

        rec = {}
        external_link = 'https://www.century21.be/nl/onze-vastgoed/details/'+proper['id']

        external_source = 'Century21spider'

        resp = requests.get(external_link)

        soup = BeautifulSoup(resp.content)

        title = (soup.find('div',attrs={"class":"property-navigation__homeinfo"}).text).replace('\n','').replace('   ','').strip()

        images = []
        for img in  proper['medias']:
            images.append('https://static.century21.be/images/original/'+img['name'])

        property_type = proper['propertyType']

        description = ''
        if soup.find('div',id='property_card_description'):
            description = soup.find('div',id='property_card_description').text.strip()
        else:
            description = ''
        rent = proper['rent']

        external_images_count = len(images)

        address = ''
        if proper['address'].has_key('streetName'):
            address = proper['address']['streetName']+' '+proper['address']['postalCode']+' '+proper['address']['cityName']
        else:
            address = 'Niet vermeld door de eigenaar'

        zipcode = proper['address']['postalCode']

        parking = False
        for dt in soup.find_all('dt',class_='information__key'):
            if 'Buitenparkeerplaats' in dt.text:
                if dt.find_next('dd').text.lower() == 'nee':
                    parking = False
                else:
                    parking = True

        swim = False
        for dt in soup.find_all('dt',class_='information__key'):
            if 'Zwembad' in dt.text:
                if dt.find_next('dd').text.lower() == 'nee':
                    swim = False
                else:
                    swim = True
        rec['external_link'] = external_link
        rec['external_source'] = external_source
        rec['title'] = title
        rec['images'] = images
        rec['property_type'] = property_type
        rec['description'] = description
        rec['rent'] = rent
        rec['external_images_count'] = external_images_count
        rec['address'] = address
        rec['zipcode'] = zipcode
        rec['city'] = proper['address']['cityName']

        ss = geolocator.geocode(proper['address']['cityName']+','+proper['address']['countryName'])
        if ss:
            rec['latitude'] = ss.latitude
            rec['longitude'] = ss.longitude
        else:
            rec['latitude'] = None
            rec['longitude'] = None
        rec.update(contact)
        rec['parking'] = parking
        rec['swimming_pool'] = swim
        rec['landlord_name'] = 'Century 21 Properties'
        result.append(rec)
    return result

def write_json():
    data = get_data()
    data = json.dumps(data)
    with open('century21.json','w') as f:
        f.write(data)

write_json()

