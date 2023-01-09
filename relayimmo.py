#!/usr/bin/env python
# coding: utf-8

import requests 
from bs4 import BeautifulSoup
import re,json
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

locator = Nominatim(user_agent="myGeocoder")


def numfromStr(text):
	list_text = re.findall(r'\d+',text)

	if len(list_text)==2:
		output = list_text[0]+list_text[1]
	elif len(list_text)==1:
		output = list_text[0]
	else:
		output=text

	return output

def getAddress(lat,lng):
	coordinates = str(lat)+","+str(lng)
	location = locator.reverse(coordinates)
	return location


def getLatLng(city,country):
	loc = locator.geocode(city+','+ country)
	return loc.latitude,loc.longitude



def getSubInfo(soup):

	terrace = False
	balcony = False
	furnished = False
	elevator = False
	swimming_pool = False
	parking = False

	title = soup.find("div",class_="col-12 col-lg-8").find("h1").text.strip()
	description = soup.find("div",class_="col-12 col-lg-8").find("p").text.strip()
	

	if "lift" in description.lower() and "geen lift" not in description.lower():
		elevator = True
	if "garage" in description.lower() or "parking" in description.lower():
		parking = True
	if "terras" in description.lower():
		terrace = True
	if "balcon" in description.lower() or "balcony" in description.lower():
		balcony = True
	if "zwembad" in description.lower() or "swimming" in description.lower():
		swimming_pool = True
	if "gemeubileerd" in description.lower()or "aménagées" in description.lower() or "furnished" in description.lower():
		furnished=True
	if "garage" in description.lower() or "parking" in description.lower():
		parking = True

	pictures = soup.find("div" ,class_="owl-carousel owl-nav-right margin-bottom-30").findAll("img",alt="")
	imgLst = []
	for pics in pictures:
		imgLst.append(pics["src"])


	if "garage" in title.lower():
		property_type="garage"
	elif "extérieur" in title.lower():
		property_type="warehouse"
	elif "bureau" in title.lower():
		property_type="Bureau"
	elif "médicaux" in title.lower():
		property_type="Bureau"
	elif "studio" in title.lower():
		property_type="Studio"
	elif "chambres" in title.lower():
		property_type="house"
	elif "appartement" in title.lower():
		property_type="appartement"
	elif "commercial" in title.lower():
		property_type="commercial"
	elif "maison" in title.lower():
		property_type="maison"
	elif "magnifique" in title.lower():
		property_type="Magnifique"
	elif "comerciale" in title.lower():
		property_type="comerciale"
	elif "entrepôts" in title.lower():
		property_type="warehouse"
	else:
		property_type = "NA"


	dic = {
		"terrace":terrace,
		"balcony":balcony,
		"furnished":furnished,
		"elevator":elevator,
		"swimming_pool":swimming_pool,
		"parking": parking,
		"title":title,
		"description":description,
		"images":imgLst,
		"external_images_count":len(imgLst),
		"landlord_name":"Relay Immo",
		"landlord_phone":"+32 (0) 69 22 90 99",
		"landlord_email":"NA",
		"property_type":property_type
	}

	return dic



def getPropInfo(list_prop):

	list_data=[]

	for propSoup in list_prop:

		city = propSoup.find("h2").text.strip()
		rent = numfromStr(propSoup.find("h4").text.strip())

		latitude,longitude = getLatLng(city,"Belgium")
		location = getAddress(latitude,longitude)
		address = location.address
		zipcode = location.raw["address"]["postcode"] 


		if propSoup.find("i",class_="flaticon-bed"):
			bedCount = numfromStr(propSoup.find("span").text.strip())
		else:
			bedCount = "NA"

		external_source = "relayimmo.be"
		external_link = "https://www.relayimmo.be/"+propSoup.find("a",class_ = "portfolio-link")["href"]

		print (external_link)
		count = 0
		while count < 5:
			try:
				response = requests.get(external_link,timeout=30)
				count = 5
			except Exception as e:
				print(e)
			count+=1



		soup = BeautifulSoup(response.content,"html.parser")
		dic_detail = getSubInfo(soup)

		dic_detail.update({"address":address,"city":city,"zipcode":zipcode,"latitude":latitude,
			"longitude":longitude,"external_link":external_link,"external_source":external_source,
			"rent":rent,"room_count":bedCount,"position":"NA"})

		list_data.append(dic_detail)
	return list_data






def scrpProptry():
	listPropties = []
	for i in range(100):
		print("page>>>>",i)
		url = "https://www.relayimmo.be/Chercher-bien-accueil--L--resultat?pagin={}&localiteS=&type=&prixmaxS=70-10000000&chambreS=&keyword=&".format(i)

		count = 0
		while count < 5:
			try:
				response = requests.get(url,timeout=30)
				count = 5
			except Exception as e:
				print(e)
			count+=1

		soup =BeautifulSoup(response.content,"html.parser")

		if soup.find("a",class_ = "portfolio-link"):
			allPropDiv = soup.findAll("div",class_="portfolio-box")[2:]
			listPropties.extend(allPropDiv)
		else:
			break

	return getPropInfo(listPropties)
	

data = json.dumps(scrpProptry())

with open('relayimmo.json','w') as f:
    f.write(data)