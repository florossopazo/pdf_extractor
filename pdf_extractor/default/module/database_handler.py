"""MySQL stuff"""
import pymongo
#from .configg import DB_CONFIG # Database user & password

myclient = pymongo.MongoClient('mongodb://localhost:27017')

# Creates database
mydb = myclient['mydatabase']

# Creates collection
mycol = mydb["documents"]

# Check if database exists!
print(myclient.list_database_names())

# OR
dblist = myclient.list_database_names()
if "mydatabase" in dblist:
    print("The database exists!")

# Check if collection exists!
print(mydb.list_collection_names())

#OR
collist = mydb.list_collection_names()
if "documents" in collist:
    print("The collection exists!")

mylist = [
    {"issue_date": "2024-12-31", "expiry_date": "2025-12-31", "document_type": "SQF Certificate"},
    {"issue_date": "2023-01-01", "expiry_date": "2024-01-01", "document_type": "FSSC 22000 Certificate"}
]

def insert_into_db(document_list):
    x = mycol.insert_many(document_list)
    print(x.inserted_ids)

