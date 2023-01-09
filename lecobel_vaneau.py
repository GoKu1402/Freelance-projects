#!/usr/bin/env python
# coding: utf-8

import requests 
from bs4 import BeautifulSoup
import re,json,time
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import ast
from pprint import pprint

locator = Nominatim(user_agent="myGeocoder")

def getAddress(lat,lng):
	coordinates = str(lat)+","+str(lng)
	location = locator.reverse(coordinates)
	return location


def numfromStr(text,flag = False):
	list_text = re.findall(r'\d+',text)

	if len(list_text)==2:
		output = list_text[0]+list_text[1]
	elif len(list_text)==1:
		output = list_text[0]
		flag = False
	else:
		output=text

	if flag:
		output = "NA"

	return output


def proptyDetail(soup):

	balcony=False
	parking=False
	terrace=False
	elevator=False
	swimming_pool=False
	furnished=False
	description = "NA"
	landlord_name = "NA"
	landlord_phone= "NA"
	landlord_email = "NA"

	if soup.find("section",id="description"):
		prortySoup = soup.find("section",id="description")
		description = prortySoup.find("div",class_="description").text.strip()
		soupstr = str(prortySoup.find("div",class_="specifications"))

		if "balcony" in soupstr.lower():
			balcony=True
		if "terrace" in soupstr.lower():
			terrace=True
		if "elevator" in soupstr.lower() or "lift" in soupstr.lower():
			elevator=True
		if "swimming" in soupstr.lower():
			swimming_pool=True
		if "furnished" in soupstr.lower() or "furnished" in description.lower():
			furnished = True

		if soup.find("div",class_="informations__agent"):#.find('div',class_="name").text.strip()
			landlord_name = soup.find("div",class_="informations__agent").find('div',class_="name").text.strip()
		else:
			landlord_name = "LECOBEL VANEAU RENTALS"

		landlord_phone = "+32 467 85 71 82"
		landlord_email = "rent@lecobel.be"

	dic = {
		"landlord_name":landlord_name,
		"landlord_phone":landlord_phone,
		"landlord_email":landlord_email,
		"swimming_pool":swimming_pool,
		"elevator":elevator,
		"terrace":terrace,
		"balcony":balcony,
		"furnished":furnished,
		"description":description
	}

	return dic




def getPropertyDetails(all_proprty):
	list_propty =[]
	for index,soup in enumerate(all_proprty):

		print (">>>>>",index)
		bedCount = "NA"
		latitude = soup["data-latitude"]
		longitude = soup["data-longitude"]


		location = getAddress(latitude,longitude)

		zipcode = location.raw["address"]["postcode"]
		address = location.address

		if "city_district" in location.raw["address"]:
			city=location.raw["address"]["city_district"]
		elif "city" in location.raw["address"]:
			city=location.raw["address"]["city"]
		elif "town" in location.raw["address"]:
			city=location.raw["address"]["town"]
		else:
			print (location.raw["address"])
			city = "NA"


		external_link = "https://www.lecobel-vaneau.be"+soup["data-url"]
		external_source = "lecobel-vaneau.be"
		title = soup.find("a",class_="link__property full-link")["title"]


		imgLst = []
		for picture in soup.findAll("source",type="image/webp"):
			imgLst.append("https://www.lecobel-vaneau.be"+(picture["srcset"]))


		price = soup.find("div",class_="property-price property-data--center").text.strip()
		rent = numfromStr(price)

		property_type = soup.find("div",class_="property-name property-data--bold property-data--center property-data--upper").text.split("-")[-1].strip()

		if soup.find("div",class_="property-bedrooms property-data--center property-data--bold"):
			bedCount = numfromStr(soup.find("div",class_="property-bedrooms property-data--center property-data--bold").text.strip(),flag=True)
			


		count = 0
		while  count < 5:
			try:
				response = requests.get(external_link,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count +=1

		print (external_link)

		soup2 = BeautifulSoup(response.content,"html.parser")

		dic_detail =proptyDetail(soup2)

		dic_detail.update({"address":address,"zipcode":zipcode,'city':city,"external_link":external_link,"title":title,
			"images":imgLst,"rent":rent,"room_count":bedCount,"property_type":property_type,
			"latitude":latitude,"longitude":longitude,"position":"NA","external_images_count":len(imgLst)})

		list_propty.append(dic_detail)

	return list_propty



def scrapDetail(url):
	count = 0
	while  count < 5:
		try:
			response = requests.get(url,timeout=30)
			count = 5
		except Exception as e:
			print (e)
		count +=1

	soup = BeautifulSoup(response.content,"html.parser")

	all_proprty = soup.findAll("div",class_="property property__search-item")

	k = 30
	while True:
		url = "https://www.lecobel-vaneau.be/en/vaneau-search/search?field_ad_type[eq][]=renting&limit=28&mode=list&offset={}&offset_additional=0&search_page_id=580".format(k)
		print (url)

		count = 0
		while  count < 5:
			try:
				response = requests.get(url,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count +=1

		jsonLoad = json.loads(response.content.decode("utf-8"))

		if len(jsonLoad["html"]) < 200:
			break
		
		soup = BeautifulSoup(jsonLoad["html"],"html.parser")
		proprtys = soup.findAll("div",class_="property property__search-item")


		all_proprty.extend(proprtys)
		k+=28



	return getPropertyDetails(all_proprty)



url = "https://www.lecobel-vaneau.be/en/list-properties-tenant"
data = json.dumps(scrapDetail(url))

with open('lecobel_vaneau.json','w') as f:
    f.write(data)