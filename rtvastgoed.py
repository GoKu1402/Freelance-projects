#!/usr/bin/env python
# coding: utf-8

import requests 
from bs4 import BeautifulSoup
import re,json
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

locator = Nominatim(user_agent="myGeocoder")


def getAddress(lat,lng):
	coordinates = lat+","+lng
	location = locator.reverse(coordinates)
	return location

def extractPrice(text):
	textlst = re.findall(r'\d+', text)
	if len(textlst)==3:
		return textlst[0]+textlst[1]
	elif len(textlst)==2:
		return textlst[0]
	elif len(textlst)==1:
		raise Exception("Anomile Price Value Please Check")
	else:
		return text

def scrapDetail(soup):
	title = soup.find("div",class_="property__header-block").find("h1").text.strip()

	address = "NA"
	bedCount = "NA"
	latitude = "NA"
	longitude = "NA"
	city="NA"
	zipcode = "NA"
	rent = "NA"
	imgLst = []

	furnished,parking,balcony, = False,False,False

	add = soup.find("div",class_="property__header-block__adress__street")
	if add:
		address = add.text.strip()
	#==================================================================================================

	img_urls = soup.find("div",class_="prop-pictures").findAll("a")
	for img in img_urls:
		imgLst.append("https://www.rtvastgoed.be"+img["href"])

	#==================================================================================================
	description = soup.find("div",class_="property__details__block__description").text.strip()
	#==================================================================================================

	financial_table = soup.find("table",class_="financial detail-fields property__details__block__table")
	if financial_table:
		if "prijs" in financial_table.find("tr",class_="even").text.strip().lower():
			rent = extractPrice(financial_table.find("tr",class_="even").find("td",class_="value").text)
	#==================================================================================================

	building_det=soup.find("table",class_="construction property__details__block__table")
	if building_det:
		if "aantal slaapkamers" in building_det.text:
			bedCount = building_det.find("tr",class_="odd").find("td",class_="value").text.strip()
	#==================================================================================================

	if "ingericht" in soup.text.lower():
		furnished = True
	if "garage" in soup.text.lower() or "parking" in soup.text.lower():
		parking = True
	#==================================================================================================


	if soup.find("div",class_="gmap",id="pand-map"):
		latitude = soup.find("div",class_="gmap",id="pand-map")["data-geolat"]
		longitude = soup.find("div",class_="gmap",id="pand-map")["data-geolong"]

		location = getAddress(latitude,longitude)
		if address == "NA":
			address = location.address
		if zipcode == "NA":
			zipcode = location.raw["address"]["postcode"]
		if city == "NA":
			city=location.raw["address"]["city_district"]

	#==================================================================================================
	if address != "NA" and latitude == "NA":
		raise Exception("Latitude and longitude Missing")

	dic = {
		"title":title,
		"description":description,
		"address":address,
		"rent":rent,
		"room_count":bedCount,
		"images":imgLst,
		"city":city,
		"furnished":furnished,
		"balcony":balcony,
		"latitude":latitude,
		"longitude":longitude,
		"zipcode":zipcode,
		"parking":parking,
		"position":"NA",
		"external_images_count":len(imgLst),
		"landlord_name":"RT VERHUUR",
		"landlord_phone":"+32 11 69 76 40",
		"landlord_email":"verhuur@rtvastgoed.be"
	}


	return dic



def getPropertyDetails(url):
	
	count = 0
	while  count < 5:
		try:
			response = requests.get(url,timeout=30)
			count = 5
		except Exception as e:
			print (e)
		count +=1

	soup = BeautifulSoup(response.content,"html.parser")

	listProperty = []
	for section in soup.findAll("section"):
		proptyList = section.find("div",class_="row").findAll("div",class_="row")

		for index,propty in enumerate(proptyList):
			print (index)
			extrnlurl="https://www.rtvastgoed.be"+propty.find("a",class_="spotlight__content__moreinfo link")["href"]

			count = 0
			while  count < 5:
				try:
					response = requests.get(extrnlurl,timeout=30)
					count = 5
				except Exception as e:
					print (e)
				count +=1

			soup = BeautifulSoup(response.content,"html.parser")

			details_dic = scrapDetail(soup)
			
			details_dic.update({"property_type":section.find("h2").text.strip(),
				"external_link":extrnlurl,
				"external_source":"rtvastgoed.be"})

			listProperty.append(details_dic)

	return listProperty


url = "https://www.rtvastgoed.be/nl/te-huur/"
data = json.dumps(getPropertyDetails(url))

with open('rtvastgoed.json','w') as f:
    f.write(data)