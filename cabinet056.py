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
	coordinates = str(lat)+","+str(lng)
	location = locator.reverse(coordinates)
	return location


def getLatLng(city,country):
	loc = locator.geocode(city+','+ country)
	return loc.latitude,loc.longitude

#============================================================================================================

def basicInfo(soup):
	parking,bedroom,rent = False,"NA","NA"
	a,b = False,False

	list_det = re.findall(r'\d+', soup.find("span").text)

	if soup.find("i",class_="flaticon-bed"):
		a=True
	if soup.find("i",class_="ti-car"):
		b=True


	if len(list_det) == 4:
		bedroom = list_det[0].strip()
		parking = True
		rent = list_det[-2].strip()+list_det[-1].strip()

	elif len(list_det) == 3:
		if a:
			bedroom = list_det[0].strip()					
		if b:
			parking = True

		if a and b:
			rent = list_det[-1].strip()
		else:
			rent = list_det[-2].strip()+list_det[-1].strip()

	elif len(list_det) == 2:
		if a:
			bedroom = list_det[0].strip()
		if b:
			parking = True

		if not a and not b:
			rent = list_det[-2].strip()+list_det[-1].strip()
		else:
			rent = list_det[-1].strip()

	else:
		rent = list_det[-1].strip()


	return bedroom,parking,rent

#============================================================================================================
def scrapDetail2(soup):
	terrace = False
	balcony = False
	furnished = False
	elevator = False
	swimming_pool = False


	title = soup.find("h1",class_="font-weight-light").text.strip()
	descrp2 = soup.find("p",align="justify").text.strip()

	tot_descrp = title+".\n"+descrp2

	if "lift" in tot_descrp.lower() and "geen lift" not in tot_descrp.lower():
		elevator = True
	if "garage" in tot_descrp.lower() or "parking" in tot_descrp.lower():
		parking = True
	if "terras" in tot_descrp.lower():
		terrace = True
	if "balcon" in tot_descrp.lower() or "balcony" in tot_descrp.lower():
		balcony = True
	if "zwembad" in tot_descrp.lower() or "swimming" in tot_descrp.lower():
		swimming_pool = True
	if "gemeubileerd" in tot_descrp.lower() or "furnished" in tot_descrp.lower():
		furnished=True


	img_div = soup.find("div",class_="owl-carousel owl-nav-overlay owl-dots-overlay margin-bottom-30").findAll("img")
	list_img=[]
	for img in img_div:
		list_img.append(img["src"])

	lanlord_no=soup.find("a",href="envoyer-un-message--contact")["title"]
	landlord_email = "NA"
	landlord_name = "Aller vers le site du DL Groupe"


	for p in soup.findAll("p"):
		if p.find("i",class_="fa fa-location-arrow"):
			address = p.find("i",class_="fa fa-location-arrow").text.strip()
			break

	if "appartement" in title.lower():
		property_type = "appartement"
	elif "garage" in title.lower():
		property_type = "garage"
	elif "maison" in title.lower():
		property_type = "maison"
	elif "commerciale" in title.lower():
		property_type = "Surface commerciale"
	elif "studio" in title.lower():
		property_type = "Studio"
	elif "bureau" in title.lower():
		property_type = "Bureau idéal"
	elif "café" in title.lower():
		property_type = "Café"
	elif "penthouse" in title.lower():
		property_type = "penthouse"
	else:
		property_type = "NA"

	dic = {
		"terrace":terrace,
		"balcony":balcony,
		"furnished":furnished,
		"elevator":elevator,
		"swimming_pool":swimming_pool,
		"description":tot_descrp,
		"images":list_img,
		"external_images_count":len(list_img),
		"landlord_name":landlord_name,
		"landlord_email":landlord_email,
		"landlord_phone":lanlord_no,
		"title":title,
		"address":address,
		"property_type":property_type
	}

	return dic

#============================================================================================================

def scrapDetail(soup):

	main_div = soup.find("div",class_="container-fluid").find("div",class_=True,recursive=False)
	if main_div:

		propertyList = main_div.findAll("div",recursive=False)
		list_data = []
		for propty in propertyList:

			extrn_link="http://www.cabinet056.be/"+propty.find("a",class_="portfolio-link")["href"]


			cityDiv = propty.find("div",class_="portfolio-title")
			city = cityDiv.find("h6").text.strip()
			
			latitude,longitude = getLatLng(city,"Belgium")
			location = getAddress(latitude,longitude)
			zipcode = location.raw["address"]["postcode"] 

			rootInfo=basicInfo(cityDiv)

			print (extrn_link)
			count = 0
			while count < 5:
				try:
					response = requests.get(extrn_link,timeout = 30)
					count = 5
				except Exception as e:
					print (e)
				count+=1

			soup2 = BeautifulSoup(response.content,"html.parser")
			dic_detail = scrapDetail2(soup2)

			dic_detail.update({"city":city,"room_count":rootInfo[0],"parking":rootInfo[1],
				"rent":rootInfo[2],"position":"NA","external_link":extrn_link,
				"external_source":"cabinet056.be","zipcode":zipcode,"latitude":latitude,
				"longitude":longitude})

			list_data.append(dic_detail)

		return list_data


#============================================================================================================

def scrapProprties(url):
	count = 0
	while count < 5:
		try:
			response = requests.get(url,timeout = 30)
			count = 5
		except Exception as e:
			print (e)
		count+=1

	soup = BeautifulSoup(response.content,"html.parser")
	pagination = soup.find("ul",class_="pagination justify-content-center margin-top-70").findAll("li")[-2]


	list_data = []
	for i in range(int(pagination.text)):
		print ("PAGE=>>>",i)

		url = "http://www.cabinet056.be/Chercher-bien-accueil--L--resultat?pagin={}&regionS=&communeS=&type=&prixmaxS=&chambreS=&keyword=&viager=&listeLots=".format(str(i))
		count = 0
		while count < 5:
			try:
				response = requests.get(url,timeout = 30)
				count = 5
			except Exception as e:
				print (e)
			count+=1

		soup = BeautifulSoup(response.content,"html.parser")
		data_ = scrapDetail(soup)

		list_data.extend(data_)

	return list_data





#============================================================================================================
url = "http://www.cabinet056.be/maison-a-vendre--L--resultat"
data = json.dumps(scrapProprties(url))

with open('cabinet056.json','w') as f:
    f.write(data)
