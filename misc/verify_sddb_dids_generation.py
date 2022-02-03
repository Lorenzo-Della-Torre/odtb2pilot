from os import abort
from bs4 import BeautifulSoup

# Reading the data inside the xml file to a variable under the name  data
try:
	with open('C:/vcc\ODTB2Pilot2\odtb2pilot/rigs\pi10\sddb/32290001AH_32290001AD_32290001AD.sddb', 'r', encoding='utf-8') as f:
		data = f.read()
except FileNotFoundError:
	print("Please add path to sddb file on line 5 in ", __file__)
	abort()

# Passing the stored data inside the beautifulsoup parser
bs_data = BeautifulSoup(data, 'xml')

# Collect all dids from sddb
nbr_of_data_identifiers_sddb = 0
sddb_dids = []
services22 = bs_data.find_all(Name = "Read Data By Identifier")
for sddb_area in services22:
	for did in sddb_area.find_all("DataIdentifier"):
		nbr_of_data_identifiers_sddb += 1
		sddb_dids.append(did.get('ID'))

# Get all dids from python sddb
try:
	from sddb_dids import app_did_dict, sbl_did_dict, pbl_did_dict
except ImportError:
	print("Please put 'sddb_dids.py' in ", __file__.split("xml_parser")[0])
	abort()

python_did_dict = dict(app_did_dict)
python_did_dict.update(sbl_did_dict)
python_did_dict.update(pbl_did_dict)
nbr_of_data_identifiers_python = 0
python_dids = []
for did_id, did_data in python_did_dict.items():
	python_dids.append(did_id)
	nbr_of_data_identifiers_python += 1


# Find what dids are missing
missing_dids = []
nbr_missing_dids = 0
for did_sddb in sddb_dids:
	if did_sddb not in python_dids:
		missing_dids.append(did_sddb)
		nbr_missing_dids += 1

# Find duplicates in sddb, this is not really relevant since some dids are present several times in the sddb.
# However, we only want to find dids that are totally missing
duplicates = []
for k in sddb_dids:
	found_once = False
	for i in sddb_dids:
		if k == i and found_once:
			duplicates.append(k)
		if k == i and not found_once:
			found_once = True

sddb_dids_no_duplicates = list(dict.fromkeys(sddb_dids))

contains_duplicates = any(sddb_dids.count(element) > 1 for element in sddb_dids)
#print("Sddb contains duplicates: ", contains_duplicates, ". Number of duplicates: ", len(duplicates))
#print("Duplicates in sddb: ", duplicates)



diff = len(sddb_dids_no_duplicates) - nbr_of_data_identifiers_python
print(f"{len(sddb_dids_no_duplicates)} dids found in sddb \n{nbr_of_data_identifiers_python} dids found in python sddb \n{diff} dids are missing." +
f"\nMissing dids found: {nbr_missing_dids}")

print("Missing dids: ", missing_dids)













# Finding all instances of tag   
# b_unique = bs_data.find_all('Version') 
# print("Version: ", b_unique) 

# Using find() to extract attributes of the first instance of the tag 
# b_name = bs_data.find('child', {'name':'Acer'}) 
# print("child: ", b_name) 