import requests
from bs4 import BeautifulSoup
import re,json

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
    resp = requests.get('https://www.athimmo.be/')
    soup = BeautifulSoup(resp.content)

    a = 'https://www.athimmo.be/'+soup.find('button',class_='btn btn-tertiary btn-for-rent').find_previous('a')['href']

    resp1 = requests.get(a)
    soup1 = BeautifulSoup(resp1.content)

    li = 'https://www.athimmo.be/'+soup1.find('link',attrs={'as':'fetch'})['href']

    resp2 = requests.get(li)

    dic  = resp2.json()

    result = []
    for rec in dic['pageContext']['data'][u'contentRow'][0]['data']['propertiesList']:
        if rec['language'] == 'fr':
            l = {}
            l['title'] = rec['TypeDescription']
            l['external_source'] = 'Athimmo2000Spider'
            l['description'] = rec['DescriptionA']
            l['room_count'] = rec['NumberOfBedRooms']
            l['rent'] = rec['Price']
            l['images'] = rec['LargePictures']
            l['city'] = rec['City']
            l['lattitude'] = rec['GoogleX']
            l['longitude'] = rec['GoogleY']
            l['landlord_name'] = 'Athimmo'
            l['landlord_phone'] = soup.find('a',title='Phone').text.strip()
            l['landlord_email'] = soup.find('a',title='Mail').text.strip()
            l['zipcode'] = rec['Zip']
            l['address'] = rec['Street']+' '+str(rec['HouseNumber'])+' '+' '+rec['Zip']+rec['City']
            l['property_type'] = rec['MainTypeName']
            if 'lift' in rec['DescriptionA'].lower() or 'elevator' in rec['DescriptionA'].lower():
                l.update({'elevator':True})
            if 'swimming' in rec['DescriptionA'].lower():
                l.update({'swimming_pool':True})
            if 'furnish' in rec['DescriptionA'].lower():
                l.update({'furnished':True})
            if 'balcony' in rec['DescriptionA'].lower():
                rec.update({'balcony':True})
            if 'parking' in rec['DescriptionA'].lower():
                l.update({'parking':True})
            l['terrace'] = rec['HasTerrace']
            l['garden'] = rec['HasGarden']
            l['external_images_count'] = len(rec['LargePictures'])
            result.append(l)
    return result

def write_json():
    data = get_data()
    data = json.dumps(data)
    with open('anthimo.json','w') as f:
        f.write(data)

write_json()
