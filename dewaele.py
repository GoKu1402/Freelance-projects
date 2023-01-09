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


def scrapeSubInfo(soup):

	terras=False
	elevator=False
	balcony=False
	furnished=False
	parking=False
	swimming_pool=False 


	description ="NA"
	landlord_name="NA"
	landlord_phone="NA"
	landlord_email="NA"


	if soup.find("div",class_="panel",id="description"):
		description = soup.find("div",class_="panel",id="description").text.strip()


		if soup.find("div",class_="responsive-table margin-bottom full-label"):
			basicInfo = soup.find("div",class_="responsive-table margin-bottom full-label").text.strip()

			if "terras" in basicInfo.lower() or "terras" in description.lower():
				terras=True
			if "autostaanplaat" in basicInfo.lower() or "autostaanplaat" in description.lower():
				parking=True
			if "lift" in description.lower() or "elevator" in description.lower():
				elevator = True
			if "balcon" in description.lower() or "balcony" in description.lower():
				balcony = True
			if "zwembad" in description.lower() or "swimming pool" in description.lower():
				swimming_pool = True
			if "gemeubileerd" in description.lower() or "furnished" in description.lower():
				furnished=True


		landlord_name = soup.find("li",class_ = "media agent").find("div",class_="bd").find("h3").text.strip()
		landlord_email = "info@dewaele.com"
		landlord_phone = "056 234 330"




	dic = {
		"terrace":terras,
		"elevator":elevator,
		"parking":parking,
		"swimming_pool":swimming_pool,
		"balcony":balcony,
		"furnished":furnished,
		"description":description,
		"landlord_phone":landlord_phone,
		"landlord_email":landlord_email,
		"landlord_name":landlord_name
	}


	return dic


def proprtyDeatil(list_data):

	listProprty = []
	for echData in list_data:

		rent=echData["sort_price"]
		zipcode = echData["a_postcode"]
		property_type = echData["subtype_woning"]
		title = echData["a_titel"]
		latitude = echData["a_geo_lat"]
		longitude = echData["a_geo_lon"]
		city = echData["a_gemeente"]
		address = echData["a_straat"]+","+zipcode+" "+city
		bedCount = echData["a_aantal_slaapkamers"]
		external_link = "https://www.dewaele.com"+echData["url_slugify"]
		external_source = "dewaele.com"

		imgLst = echData["lazyload"]
		if echData["picture_url"]:
			imgLst.append(echData["picture_url"])


		print (external_link)

		count = 0
		while count < 5:
			try:
				response = requests.get(external_link,timeout=30)
				count = 5
			except Exception as e:
				print (e)
			count+=1

		soup = BeautifulSoup(response.content,"html.parser")

		dic_details = scrapeSubInfo(soup)


		dic_details.update({"rent":rent,"zipcode":zipcode,"property_type":property_type,"title":title,
			"latitude":latitude,"longitude":longitude,"city":city,"address":address,
			"room_count":bedCount,"external_link":external_link,"external_source":external_source,
			"position":"NA","external_images_count":len(imgLst),"images":imgLst})

		listProprty.append(dic_details)

	return listProprty




def scrapDetail(url):

	headers={
		"origin": "https://www.dewaele.com",
		"referer": "https://www.dewaele.com/nl/te-huur?hash=ZmlsdGVyW3JlZ2lvbl9sb25nXT0wJmZpbHRlcltyZWdpb25fbGF0XT0wJmZpbHRlcltzdGF0dXNfdHlwZV09MyZmaWx0ZXJbbGFuZ3VhZ2VdPW5sJmZpbHRlcltlX2lkXT00NjM5NSZmaWx0ZXJbZGlyXT1kZXNjJmZpbHRlcltvcmRlcl09aXNfbmV3JmZpbHRlclttaW5fcmVudF9wcmljZV09MCZmaWx0ZXJbbWF4X3JlbnRfcHJpY2VdPTAmZmlsdGVyW2Jkcm1zXT0wJmZpbHRlclttaW5fYndfb3BwXT0wJmZpbHRlclttYXhfYndfb3BwXT0wJmZpbHRlclttaW5fZ19vcHBdPTAmZmlsdGVyW21heF9nX29wcF09MCZmaWx0ZXJbcGFnZV09MQ%3D%3D&page=1",
		"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
		"X-Requested-With": "XMLHttpRequest"
	}

	count = 0
	while count < 5:
		try:
			response = requests.get(url,headers=headers,timeout = 30)
			count = 5
		except Exception as e:
			print (e)
		count+=1


	json_load = json.loads(response.content.decode("utf-8"))

	totpage = json_load["total"]/12
	temp_page = json_load["total"]//12

	if totpage != temp_page:
		totpage = int(totpage)+1
	else:
		totpage = int(totpage)


	totProprty = []
	for page in range(1,totpage+1):
		print (">>>>>>>",page)

		strTobyte = str.encode("page="+str(page))
		base64txt = base64.b64encode(strTobyte)
		url = "https://www.dewaele.com/?ACT=108&cache=off&hash=JmZpbHRlcltyZWdpb25dPSZmaWx0ZXJbcmVnaW9uX2xvbmddPTAmZmlsdGVyW3JlZ2lvbl9sYXRdPTAmZmlsdGVyW3N0YXR1c190eXBlXT0zJmZpbHRlcltwb3N0YWxdPSZmaWx0ZXJbY2l0eV09JmZpbHRlcltwYXJlbnRfY2l0eV09JmZpbHRlcltwYXJlbnRfbGFiZWxdPSZmaWx0ZXJbZl9jXT0mZmlsdGVyW2xhbmd1YWdlXT1ubCZmaWx0ZXJbZV9pZF09NDYzOTUmZmlsdGVyW2Rpcl09ZGVzYyZmaWx0ZXJbb3JkZXJdPWlzX25ldyZmaWx0ZXJbbWluX3ByaWNlXT0mZmlsdGVyW21heF9wcmljZV09JmZpbHRlclttaW5fcmVudF9wcmljZV09MCZmaWx0ZXJbbWF4X3JlbnRfcHJpY2VdPTAmZmlsdGVyW2Jkcm1zXT0wJmZpbHRlclt0eXBlXT0mZmlsdGVyW2JfaWRdPSZmaWx0ZXJbbWluX2J3X29wcF09MCZmaWx0ZXJbbWF4X2J3X29wcF09MCZmaWx0ZXJbbWluX2dfb3BwXT0wJmZpbHRlclttYXhfZ19vcHBdPTAmZmlsdGVyW2tleXdvcmRzXT0m{}".format(base64txt.decode("utf-8"))
		headers={
			"origin": "https://www.dewaele.com",
			"referer": "https://www.dewaele.com/nl/te-huur?hash=ZmlsdGVyW3JlZ2lvbl9sb25nXT0wJmZpbHRlcltyZWdpb25fbGF0XT0wJmZpbHRlcltzdGF0dXNfdHlwZV09MyZmaWx0ZXJbbGFuZ3VhZ2VdPW5sJmZpbHRlcltlX2lkXT00NjM5NSZmaWx0ZXJbZGlyXT1kZXNjJmZpbHRlcltvcmRlcl09aXNfbmV3JmZpbHRlclttaW5fcmVudF9wcmljZV09MCZmaWx0ZXJbbWF4X3JlbnRfcHJpY2VdPTAmZmlsdGVyW2Jkcm1zXT0wJmZpbHRlclttaW5fYndfb3BwXT0wJmZpbHRlclttYXhfYndfb3BwXT0wJmZpbHRlclttaW5fZ19vcHBdPTAmZmlsdGVyW21heF9nX29wcF09MCZmaWx0ZXJbcGFnZV09MQ%3D%3D&page={}".format(page),
			"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
			"X-Requested-With": "XMLHttpRequest"
		}

		count = 0
		while count < 5:
			try:
				response = requests.get(url,headers=headers,timeout = 30)
				count = 5
			except Exception as e:
				print (e)
			count+=1

		json_load = json.loads(response.content.decode("utf-8"))
		totProprty.extend(json_load["properties"])


	return proprtyDeatil(totProprty)



url = "https://www.dewaele.com/?ACT=108&cache=off&hash=JmZpbHRlcltyZWdpb25dPSZmaWx0ZXJbcmVnaW9uX2xvbmddPTAmZmlsdGVyW3JlZ2lvbl9sYXRdPTAmZmlsdGVyW3N0YXR1c190eXBlXT0zJmZpbHRlcltwb3N0YWxdPSZmaWx0ZXJbY2l0eV09JmZpbHRlcltwYXJlbnRfY2l0eV09JmZpbHRlcltwYXJlbnRfbGFiZWxdPSZmaWx0ZXJbZl9jXT0mZmlsdGVyW2xhbmd1YWdlXT1ubCZmaWx0ZXJbZV9pZF09NDYzOTUmZmlsdGVyW2Rpcl09ZGVzYyZmaWx0ZXJbb3JkZXJdPWlzX25ldyZmaWx0ZXJbbWluX3ByaWNlXT0mZmlsdGVyW21heF9wcmljZV09JmZpbHRlclttaW5fcmVudF9wcmljZV09MCZmaWx0ZXJbbWF4X3JlbnRfcHJpY2VdPTAmZmlsdGVyW2Jkcm1zXT0wJmZpbHRlclt0eXBlXT0mZmlsdGVyW2JfaWRdPSZmaWx0ZXJbbWluX2J3X29wcF09MCZmaWx0ZXJbbWF4X2J3X29wcF09MCZmaWx0ZXJbbWluX2dfb3BwXT0wJmZpbHRlclttYXhfZ19vcHBdPTAmZmlsdGVyW2tleXdvcmRzXT0mcGFnZT0y"
data = json.dumps(scrapDetail(url))

with open('dewaele.json','w') as f:
    f.write(data)