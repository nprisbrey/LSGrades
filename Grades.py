from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from math import floor, ceil
from tqdm import tqdm
from os.path import exists
from cryptography.fernet import Fernet
import base64
import re
import os

CREDS_FILE = "GradeCredentials.gcreds"
USERID = None
PASSWD = None
PAGE_LOAD_TIME = 3

def createCreds():
	print("Please enter the following information:")
	username = input("Username: ")
	password = input("Password: ")
	key = input("Encryption Key you'll remember: ")

	cipher_suite = Fernet(base64.urlsafe_b64encode((key*(32//len(key) + 1))[:32].encode()))

	with open(CREDS_FILE,"w") as creds_file:
		creds_file.write(cipher_suite.encrypt(username.encode()).decode() + "\n")
		creds_file.write(cipher_suite.encrypt(password.encode()).decode())

	print(f"Credentials stored in '{CREDS_FILE}' successfully!")

	return username, password

def readCreds():
	if not exists(CREDS_FILE):
		raise Exception("Can't read the credentials file if it doesn't exists!")

	print("Please enter your Encryption Key:")
	key = input("Encryption Key: ")

	cipher_suite = Fernet(base64.urlsafe_b64encode((key*(32//len(key) + 1))[:32].encode()))

	with open(CREDS_FILE,"r") as creds_file:
		info = creds_file.readlines()
		username = cipher_suite.decrypt(info[0].strip().encode())
		password = cipher_suite.decrypt(info[1].strip().encode())

	print("Successfully grabbed the information from the credential file.")

	return username.decode(), password.decode()

def centerTxt(text,width):
	if len(str(text)) > width:
		raise Exception(f"Given '{text}' when longer than given width {width}")
	return " "*floor((width-len(str(text)))/2) + str(text) + " "*ceil((width-len(str(text)))/2)

def getGrade(browser,page,howManyClasses):
	browser.get(page)
	sleep(PAGE_LOAD_TIME)

	# If a Learning Suite class
	if "learningsuite.byu.edu" in browser.current_url.lower():
		for i in range(1,howManyClasses + 1):
			try:
				overallGrade = browser.find_element(By.ID, "currentPercent" + str(i))
				return overallGrade.text.strip().split()[-1], page
			except:
				pass
		raise Exception(f"We could never find the overall grade on the {page} page.")

	# If a Canvas class
	elif "byu.instructure.com" in browser.current_url.lower():
		# If not already on the grades page
		if browser.current_url[-6:] != "grades":
			# Change to the "grades" page
			browser.get(browser.current_url + "/grades")
			sleep(PAGE_LOAD_TIME)

		# Find the row of the final grade
		overallGrade = browser.find_element(By.ID, "submission_final-grade").find_element(By.CLASS_NAME,"grade")
		return overallGrade.text.strip(), browser.current_url

	else:
		raise Expection("Do you have a class that's not a Learning Suite nor Canvas class?!?")

def printGrades(class_dict,column_widths):
	print()
	print(centerTxt("NUMBER",column_widths["NUMBER"]) + "|" + centerTxt("CLASS",column_widths["CLASS"]) + "|" + centerTxt("NAME",column_widths["NAME"]) + "|" + centerTxt("GRADE",column_widths["GRADE"]))
	print("-"*(sum([x for x in column_widths.values()]) + len(column_widths) - 1))
	for cls in class_dict:
		print(centerTxt(list(class_dict.keys()).index(cls)+1,column_widths["NUMBER"]) + "|" + centerTxt(cls,column_widths["CLASS"]) + "|" + centerTxt(class_dict[cls][0],column_widths["NAME"]) + "|" + centerTxt(class_dict[cls][2],column_widths["GRADE"]))

# Prompt user for how long to load each page
userLoadTime = input("Please enter how many seconds it takes to load a webpage. Press 'ENTER' to use 3 seconds: ")
try:
	userLoadTime = int(userLoadTime)
	if userLoadTime < 0:
		print("Load time must be more than 0 seconds. Defaulting to 3 seconds...")
	else:
		PAGE_LOAD_TIME = userLoadTime
except:
	print(f"Error using value '{userLoadTime}' as seconds for page load. Defaulting to 3 seconds.")

# Check if encrypted credentials are already stored
if exists(CREDS_FILE):
	print("You already have login credentials stored. Would you like to do?")
	userChoice = input("Use/New/Erase/Skip: ")

	# Use previously stored credentials
	if userChoice.lower() == "use" or userChoice.lower() == "u":
		USERID, PASSWD = readCreds()

	# Create new credentials
	elif userChoice.lower() == "new" or userChoice.lower() == "n":
		USERID, PASSWD = createCreds()

	# Erase previous credentials
	elif userChoice.lower() == "erase" or userChoice.lower() == "e":
		try:
			os.remove(CREDS_FILE)
			print(f"'{CREDS_FILE}' removed successfully")
		except:
			print(f"Couldn't remove '{CREDS_FILE}'! You'll have to do it yourself.")

	# Skip any credential usage and continue without
	elif userChoice.lower() == "skip" or userChoice.lower() == "s":
		print("Continuing onwards without using the stored credentials...")

	else:
		print(f"'{userChoice}' isn't a valid option. We'll continue on as normal.")

# If encrypted credentials aren't already stored
else:
	print("Would you like to store your login credentials locally for future use?")
	userChoice = input("Yes/No: ")

	if userChoice.lower() == "yes" or userChoice.lower() == "y":
		USERID, PASSWD = createCreds()
	else:
		print("No worries! Continuing on...")


browser = webdriver.Firefox()
browser.get("https://learningsuite.byu.edu")

# If we have cached credentials
if USERID and PASSWD:
	sleep(PAGE_LOAD_TIME)

	# Enter credentials
	uField = browser.find_element(By.ID, "username")
	uField.send_keys(USERID)
	pField = browser.find_element(By.ID, "password")
	pField.send_keys(PASSWD)

	# Click the submit button
	browser.find_element(By.ID, "byuSignInButton").click()

	print("PLEASE FINISH SIGNING IN")

# If no cached credentials
else:
	print("PLEASE LOGIN IN THE POPUP WINDOW")

while browser.title != "BYU Learning Suite":
	sleep(1)

print("PLEASE WAIT WHILE FINDING GRADES")

sleep(PAGE_LOAD_TIME)

# If in Instructor mode, switch to Student View
if ">Go to Student View</a>" in browser.page_source:
	browser.find_element(By.ID, "change-view").click()
	sleep(PAGE_LOAD_TIME)

class_strings = set(re.findall('cid-\S*/student/home">.*</a>',browser.page_source))

# Holds all of the information for each class in form of "CLASS":["NAME",gradesLink,grade]
class_dict = {}
for info in class_strings:
	cClass = re.search('">.*</a>',info).group()[2:-4]
	cClass = cClass[:cClass.find(" - ")]
	cName = re.search('">.*</a>',info).group()[2:-4][len(cClass)+2:].strip()
	cURL = "https://learningsuite.byu.edu/" + re.search("cid-\S*/student/",info).group() + "gradebook"
	class_dict[cClass] = [cName,cURL]

# Add grade to class_dict for each class
print("Class progress:")
for cls in tqdm(class_dict):
	grade, gradesLink = getGrade(browser,class_dict[cls][1],len(class_dict))

	# Update information in class_dict
	class_dict[cls][1] = gradesLink
	class_dict[cls].append(grade)

# Calculates the widths of each column based upon the maximum entry
column_widths = {"NUMBER":8,"CLASS":len(max(list(class_dict.keys()),key=len))+2,"NAME":len(max([x[0] for x in class_dict.values()],key=len))+2,"GRADE":9}

# Enter an infinite loop to interact with the user
while True:
	printGrades(class_dict,column_widths)
	classNum = input("Number of Class to view (blank to exit): ")
	if classNum == "":
		quit()
	else:
		try:
			classNum = int(classNum)
			if classNum < 1 or classNum > len(class_dict):
				print(f"\n'{classNum}' isn't a valid class number. Please enter nothing or a number between 1 and {len(class_dict)}.")
				sleep(1)
				continue
			browser.get(class_dict[list(class_dict.keys())[classNum-1]][1])
		except:
			print(f"\nCan't recongize '{classNum}'. Please enter nothing or a number between 1 and {len(class_dict)}.")
			sleep(1)
