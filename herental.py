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
    resp = requests.get('https://www.heylenvastgoed.be/nl/te-huur')

    soup =BeautifulSoup(resp.content)

    offices = []
    for l in soup.find('div',id='offices__footer').find_all('li'):
        offices.append({'city':l.strong.text,'telephone':l.text.replace(l.strong.text,'').strip()})

    landlord_phone = soup.find('ul',id='sub__nav').find('a',class_=re.compile('mobile')).text
    landlord_email = soup.find('ul',id='sub__nav').find('a',class_=re.compile('mail')).text
    landlord_name = 'Heylen Vastgoed Herentals'

    result=[]
    lix = 'https://www.heylenvastgoed.be/nl/te-huur/in-herentals/pagina-'
    i = 1
    while True:
        url = lix+str(i)
        resp1 = requests.get(url)
        if resp1.status_code !=200:
            break
        print url
        soup1 = BeautifulSoup(resp1.content)
        i = i+1
        for li in soup1.find('section',id='properties__list').find('ul').find_all('li',recursive=False):
            if not li.find('a',class_='property-contents'):
                continue
        #     print li
            rec = {}
            property_type = li.find('p',class_='category').text
            rent = li.find('p',class_='price').text
            city = li.find('p',class_='city').text
            room_count = 0
            if li.find('li',class_='rooms'):
                room_count = li.find('li',class_='rooms').text
            else:
                room_count = 0
            external_link = li.find('a',class_='property-contents')['href']
            resp2 = requests.get(external_link)
            soup2 = BeautifulSoup(resp2.content)


            address = soup2.find('section',id='property__title').find('div',class_='address').text.replace('Adres:','')

            title = soup2.find('section',id='property__title').find('div',class_='name').text

            description = soup2.find('div',id='description').text

            ss = geolocator.geocode(city)


            rec['property_type'] =property_type
            rec['rent'] =rent
            rec['city'] =city
            rec['room_count'] =room_count
            rec['external_link'] =external_link
            rec['external_source'] = 'Heylen Vastgoed Herentals Spider'
            rec['address'] =address

            rec['title'] =title

            rec['description'] =description
            if ss:
                rec['latitude'] = ss.latitude
                rec['longitude'] = ss.longitude
            else:
                rec['latitude'] = None
                rec['longitude'] = None
            rec['landlord_phone'] = landlord_phone
            rec['landlord_email'] = landlord_email
            rec['landlord_name'] = landlord_name
            rec['offices'] = offices
            rec['zipcode'] = None

            if soup2.find('div',class_='detail garage-details') and 'buitenparking' in soup2.find('div',class_='detail garage-details').text:
                rec['parking'] =True
            else:
                rec['parking'] =False

            if soup2.find('div',class_='detail layout-details') and 'terras' in soup2.find('div',class_='detail layout-details').text:
                rec['terrace'] = True
            else:
                rec['terrace'] =False
            soup2.find('section',id='property__photos').find_all('a')

            images = []
            for a in soup2.find('section',id='property__photos').find_all('a'):
                images.append(a['href'])
            rec['images'] = images
            rec['external_images_count'] = len(images)
            result.append(rec)
    return result

def write_json():
    data = get_data()
    data = json.dumps(data)
    with open('theherental.json','w') as f:
        f.write(data)
write_json()