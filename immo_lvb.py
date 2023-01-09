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

def getImgList(soup):

	imgUrls = soup.findAll("meta" ,property="og:image")

	imgLst = []

	for img in imgUrls:
		imgLst.append(img["content"])


	return imgLst


#============================================================================================================

def scrapePropDetail(listPropty):

	list_data = []
	for index,echData in enumerate(listPropty):

		print(">>>>>>>",index)

		balcony = False
		parking = False
		elevator = False
		swimming_pool =False
		terrace = False
		furnished = False

		external_link = "https://www.immo-lvb.be/nl"+echData["Property_URL"]
		external_source="immo-lvb.be"
		zipcode = echData["Property_Zip"]
		city =echData["Property_City_Value"]
		description=echData["Property_Description"]
		bedCount = echData["bedrooms"]
		property_type = echData["Property_HeadType_Value"]
		latitude = echData["Property_Lat"]
		longitude=echData["Property_Lon"]
		rent = numfromStr(echData["Property_Price"])
		title = echData["Property_Title"]
		address = echData["Property_Reference"]+","+zipcode+" "+city
		landlord_name = "Katrien Kerckaert"
		landlord_phone = "+32 56 21 81 00"
		landlord_email = "info@immo-lvb.be"


		if "garage" in description.lower() or "parkeerplaat" in description.lower():
			parking=True
		if "lift" in description.lower() or "elevator" in description.lower():
			elevator = True
		if "terras" in description.lower():
			terrace = True
		if "balcon" in description.lower() or "balcony" in description.lower():
			balcony = True
		if "zwembad" in description.lower() or "swimming pool" in description.lower():
			swimming_pool = True
		if "gemeubileerd" in description.lower() or "furnished" in description.lower():
			furnished=True

		count = 0
		while count < 5:
			try:
				response = requests.get(external_link,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count+=1


		soup = BeautifulSoup(response.content,"html.parser")
		imgLst = getImgList(soup)

		dic = {
			"address":address,
			"city":city,
			"zipcode":zipcode,
			"rent":rent,
			"latitude":latitude,
			"longitude":longitude,
			"landlord_name":landlord_name,
			"landlord_email":landlord_email,
			"title":title,
			"description":description,
			"terrace":terrace,
			"balcony":balcony,
			"furnished":furnished,
			"property_type":property_type,
			"images":imgLst,
			"external_link":external_link,
			"external_source":external_source,
			"external_images_count":len(imgLst),
			"room_count":bedCount,
			"swimming_pool":swimming_pool,
			"elevator":elevator,
			"position":"NA"
		}

		list_data.append(dic)

	return list_data

#============================================================================================================


def scrapProprty(url):

	count = 0
	while count < 5:
		try:
			response = requests.get(url,timeout=30)
			count = 5
		except Exception as e:
			print (e)
		count+=1

	m = re.search('var mediatoken(.+?);', response.content.decode("utf-8"))
	text = m.group(1)
	tokenVal = text.strip().strip("=").strip()


	listPropty = []
	for i in range(1,100):

		url = "https://www.immo-lvb.be/Modules/ZoekModule/RESTService/SearchService.svc/GetPropertiesJSON/0/0"

		data = {"Transaction":"2","Type":"0","City":"0","MinPrice":"0","MaxPrice":"0","MinSurface":"0","MaxSurface":"0","MinSurfaceGround":"0","MaxSurfaceGround":"0",
		"MinBedrooms":"0","MaxBedrooms":"0","Radius":"0","NumResults":"15","StartIndex":i,"ExtraSQL":"0","ExtraSQLFilters":"0","NavigationItem":"0","PageName":"0",
		"Language":"NL","CountryInclude":"0","CountryExclude":"0","Token":"YPFHLEWQXCTQYUHJEYGQUQTQENJRSSQPLEXHMCNUKBJXVLZMUU","SortField":"1","OrderBy":1,"UsePriceClass":False,
		"PriceClass":"0","SliderItem":"0","SliderStep":"0","CompanyID":"0","SQLType":"3","MediaID":"0","PropertyName":"0","PropertyID":"0","ShowProjects":False,
		"Region":"0","currentPage":"0","homeSearch":"0","officeID":"0","menuIDUmbraco":"0","investment":False,"useCheckBoxes":False,"CheckedTypes":"0","newbuilding":False,
		"bedrooms":0,"latitude":"0","longitude":"0","ShowChildrenInsteadOfProject":False,"state":"0","FilterOutTypes":""}


		count = 0
		while count < 5:
			try:
				response = requests.post(url,json=data,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count+=1

		list_data = (json.loads(response.content.decode("utf-8")))

		if len(list_data) > 0:
			listPropty.extend(list_data)
		else:
			break


	return scrapePropDetail(listPropty)



#============================================================================================================
url = "https://www.immo-lvb.be/nl/te-huur/"
data = json.dumps(scrapProprty(url))

with open('immo_lvb.json','w') as f:
    f.write(data)