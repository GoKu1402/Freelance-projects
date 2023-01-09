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

def scrapDetail(soup):
	imgLst = []
	
	latlan = soup.find("div",class_="s-small-slider__text").find("div",class_="s-text-markup").find("a")["href"].split("query=")[-1]
	latitude = latlan.split(",")[0]
	longitude = latlan.split(",")[-1]

	location = getAddress(latitude,longitude)
	zipcode = location.raw["address"]["postcode"]



	descp_div = soup.find("div",class_="s-container--small")
	if descp_div:
		description = descp_div.find("div",class_="s-text-markup s-text-container-centered").text.strip()

	imgUrls = soup.find("div",class_="s-small-slider__items").findAll("a")
	for imgs in imgUrls:
		imgLst.append(imgs["href"])

	dic = {
		"latitude":latitude,
		"longitude":longitude,
		"zipcode":zipcode,
		"description":description,
		"images":imgLst,
		"external_images_count":len(imgLst),
		"landlord_name":"Agence Van den Abeele",
		"landlord_email":"info@agencevandenabeele.be",
		"landlord_phone":"050 33 39 76"
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

	json_load = json.loads(response.content.decode("utf-8"))


	list_proprty=[]
	for index,propty in enumerate(json_load["data"]):

		print (">>>>>",index)

		parking = False
		balcony = False
		furnished = False

		dump_data = json.dumps(propty).lower()


		external_link = propty["url"]
		title = propty["title"]
		bedroom = propty["bedrooms"]
		city = propty["city"]
		rent = propty["price"]
		proptyType = propty["typeSlug"]
		external_source = "agencevandenabeele.be"

		textlist =  propty["slug"].lower().split(city.lower())
		address = textlist[0]+city

		if "garage" in dump_data or "parking" in dump_data:
			parking  = True
		if "inrichten" in dump_data or "furnished" in dump_data:
			furnished = True

		count = 0
		while  count < 5:
			try:
				response = requests.get(external_link,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count +=1

		soup = BeautifulSoup(response.content,"html.parser")

		dic_details = scrapDetail(soup)

		dic_details.update({"title":title,"external_link":external_link,"room_count":bedroom,
			"city":city,"property_type":proptyType,"external_source":external_source,"address":address,
			"furnished":furnished,"balcony":balcony,"parking":parking,"rent":rent,"position":"NA"})

		list_proprty.append(dic_details)

	return list_proprty



url = "https://www.agencevandenabeele.be/nl/api/properties.json?grid=1240,1599&pg=1"

data = json.dumps(getPropertyDetails(url))

with open('agencevandenabeele.json','w') as f:
    f.write(data)