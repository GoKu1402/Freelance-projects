#!/usr/bin/env python
# coding: utf-8

import requests 
from bs4 import BeautifulSoup
import re,json
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import ast
from pprint import pprint
import base64

locator = Nominatim(user_agent="myGeocoder")

def getAddress(lat,lng):
	coordinates = str(lat)+","+str(lng)
	location = locator.reverse(coordinates)
	return location


def numfromStr(text):
	list_text = re.findall(r'\d+',text)

	if len(list_text)==2:
		output = list_text[0]+list_text[1]
	elif len(list_text)==1:
		output = list_text[0]
	else:
		output=text

	return output


#============================================================================================================

def getSubInfo(soup):

	bedCount = "NA"
	landlord_name = "NA"
	landlord_email="NA"
	landlord_phone="NA"

	terrace = False
	balcony = False
	parking = False
	furnished = False
	elevator = False
	swimming_pool = False


	title = soup.find("div",class_="row divDetailTxt").find("div",class_="col-md-4").find("h1").text.strip()


	if soup.find("i", class_ = "icon-icons_bed"):
		bedCount = soup.findAll("span",class_ = "spnTxt")[1].text.strip()

	description = soup.find("div",class_ = "divTxt").text.strip()

	if "lift" in description.lower() and "geen lift" not in description.lower():
		elevator = True
	if "garage" in description.lower():
		parking = True
	if "terras" in description.lower():
		terrace = True
	if "balcon" in description.lower() or "balcony" in description.lower():
		balcony = True
	if "zwembad" in description.lower() or "swimming pool" in description.lower():
		swimming_pool = True
	if "gemeubileerd" in description.lower() or "furnished" in description.lower():
		furnished=True

	landlordDiv = soup.find("div",class_="divSR")
	if landlordDiv:
		landlord_name = landlordDiv.find("h3").text.strip()
		landlord_email = landlordDiv.find("a",title = "email").text.strip()
		landlord_phone  = landlordDiv.find("a",title = "tel").text.strip()


	imgLst = []
	pictures = soup.findAll("picture", class_ = "")
	for pics in pictures:
		imgLst.append(pics.find("img")["src"])


	dic = {
		"title":title,
		"room_count" : bedCount,
		"terrace" : terrace,
		"balcony" : balcony,
		"parking" : parking,
		"furnished" : furnished,
		"elevator" : elevator,
		"swimming_pool" : swimming_pool,
		"description" : description,
		"images" : imgLst,
		"external_images_count" : len(imgLst),
		"landlord_name" : landlord_name,
		"landlord_email" : landlord_email,
		"landlord_phone" : landlord_phone
	}

	return dic


#============================================================================================================

def getProptyInfo(list_propty):

	list_data=[]
	for index,eachData in enumerate(list_propty):

		print (">>>>>>",index)
		zipcode = "NA"

		address = eachData["address"]
		city = eachData["city"]
		rent = numfromStr(eachData["price"])
		external_link = "https://www.vastgoedsinnaeve.be"+eachData["detailLink"]
		external_source = "vastgoedsinnaeve.be"
		property_type=eachData["type"]
		latitude = eachData["latitude"]
		longitude = eachData["longitude"]

		print (external_link)

		if latitude and longitude:
			location = getAddress(latitude,longitude)
			zipcode = location.raw["address"]["postcode"]

		count = 0
		while count < 5:
			try:
				response = requests.get(external_link)
				count = 5
			except Exception as e:
				print (e)
			count +=1

		soup = BeautifulSoup(response.content,"html.parser")
		dic_details=getSubInfo(soup)

		dic_details.update({"address":address,"city":city,"rent":rent,"external_link":external_link,
			"external_source":external_source,"property_type":property_type,"latitude":latitude,
			"longitude":longitude,"zipcode":zipcode,"position":"NA"})


		list_data.append(dic_details)
	return list_data


#============================================================================================================

def getProprtyDetail(url):

	count = 0
	while count < 5:
		try:
			response = requests.get(url,timeout = 30)
			count = 5
		except Exception as e:
			print (e)
		count +=1


	m = re.search('var infoPubs(.+?);', response.content.decode("utf-8"))
	text = m.group(1)
	jsnVal = text.strip().strip("=").strip()

	proplst = json.loads(jsnVal)

	return getProptyInfo(proplst)


#============================================================================================================
url = "https://www.vastgoedsinnaeve.be/te-huur?pageindex=1"
data = json.dumps(getProprtyDetail(url))

with open('vastgoedsinnaeve.json','w') as f:
    f.write(data)