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

locator = Nominatim(user_agent="myGeocoder")


def getAddress(lat,lng):
	coordinates = str(lat)+","+str(lng)
	location = locator.reverse(coordinates)
	return location


def cleanText(text):
	text = ''.join(text.split())
	text = re.sub(r'[^a-zA-Z0-9]', ' ', text).strip()
	return text.replace(" ","_").lower()



def cleanKey(data):
	if isinstance(data,dict):
		dic = {}
		for k,v in data.items():
			dic[cleanText(k)]=cleanKey(v)
		return dic
	else:
		return data

def latlong(text):
	res = ast.literal_eval(text)
	lat=res[0][1]
	lon=res[0][2]
	return lat,lon 

def scrapDetail(soup):


	address = "NA"
	property_type = "NA"
	bedCount = "NA"
	rent = "NA"

	parking= False
	balcony= False
	furnished= False
	terrace=False
	elevator=False


	strSoup = str(soup)

	descrpt1 = soup.find("div",class_="eleven columns alpha").find("section").find("h2").text.strip()
	descrpt2 = soup.find("div",class_="eleven columns alpha").find("section").find("p",class_="description").text.strip()
	description = descrpt1+"\n"+descrpt2


	all_tables = soup.findAll("table",class_="kenmerken")
	temp_dic = {}
	for table in all_tables:
		tds_keys = table.findAll("td",class_="kenmerklabel")
		tds_vals = table.findAll("td",class_="kenmerk")

		keys = [tag.text.strip() for tag in tds_keys]
		vals = [tag.text.strip() for tag in tds_vals]

		temp_dic.update(dict(zip(keys, vals)))

	temp_dic = cleanKey(temp_dic)

	if "adres" in temp_dic:
		address = temp_dic["adres"]
	if "terras" in temp_dic:
		terrace = True
	if "slaapkamers" in temp_dic:
		bedCount = temp_dic["slaapkamers"]
	if "prijs" in temp_dic:
		rent = re.findall(r'\d+', temp_dic["prijs"])[0]
	if "parking" in temp_dic:
		parking = True
	if "type" in temp_dic:
		property_type = temp_dic["type"]
	if "lift" in temp_dic:
		elevator = True
	

	m = re.search('infoPanden(.+?);', strSoup)
	text = m.group(1)
	textLst = text.strip().strip("=").strip()

	latitude,longitude=latlong(textLst)

	location = getAddress(latitude,longitude)
	zipcode = location.raw["address"]["postcode"]
	city=location.raw["address"]["city_district"]


	picturesLs = soup.find("div",	class_="eleven columns alpha").findAll("a",class_='slick_link',href=True)
	imgLst = []
	for img in picturesLs:
		imgLst.append(img["href"])

	dic = {
		"address":address,
		"description":description,
		"images":imgLst,
		"elevator":elevator,
		"property_type":property_type,
		"parking":parking,
		"rent":rent,
		"room_count":bedCount,
		"terrace":terrace,
		"address":address,
		"balcony":balcony,
		"furnished":furnished,
		"latitude":latitude,
		"longitude":longitude,
		"landlord_name":"IMMO ROBA",
		"landlord_phone":"09 / 388.53.53 (ZULTE OFFICE) 056 / 140.200",
		"landlord_email":"info@immoroba.be",
		"zipcode":zipcode,
		"city":city,
		"external_images_count":len(imgLst),
		"position":"NA"
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
	all_page = soup.find("div",class_="paging").findAll("div",class_="paging-box")[-2].text.strip()


	list_property = []
	for page in range(1,int(all_page)+1):

		print ("page >>>>>",page)

		url = "http://www.immoroba.be/te-huur?pageindex={}".format(str(page))
		count = 0
		while  count < 5:
			try:
				response = requests.get(url,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count +=1

		soup = BeautifulSoup(response.content,"html.parser")

		all_proprty = soup.find("div",class_="container offer").findAll("div",id=True,recursive=False)



		for proprty in all_proprty:

			if  proprty.find("a",class_="img"):

				external_link = "http://www.immoroba.be"+proprty.find("a",class_="img")["href"]
				external_source = "immoroba.be"

				title = proprty.find("div",class_="info").find("h3").text.strip()

				count = 0
				while  count < 5:
					try:
						response = requests.get(external_link,timeout=30)
						count = 5
					except Exception as e:
						print (e)
					count +=1

				soup2 = BeautifulSoup(response.content,"html.parser")


				dict_detail = scrapDetail(soup2)

				dict_detail.update({"external_link":external_link,"external_source":external_source})

				list_property.append(dict_detail)

	return list_property




url = "http://www.immoroba.be/te-huur"

data = json.dumps(getPropertyDetails(url))

with open('immoroba.json','w') as f:
    f.write(data)