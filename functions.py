import pymongo
import dns
import datetime
from flask import session
from bson.objectid import ObjectId
import urllib
import requests
import json
import os
from better_profanity import profanity
profanity.load_censor_words()

clientm = pymongo.MongoClient(os.getenv("clientm"))
usersdb = clientm.Users
profilescol = usersdb.Profiles
sdb = clientm.Scenarios
scol = sdb.Scenarios
nvscol = sdb.NotVerified
ccol = sdb.Comments

def addcookie(key, value):
  session[key] = value

def delcookies():
  session.clear()

def getcookie(key):
  try:
    if (x := session.get(key)):
      return x
    else:
      return False
  except:
    return False

def get_user(user_id):
  myquery = {"_id": int(user_id)}
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    return x
  return False

def get_user_from_username(username):
  myquery = {"Username": username}
  mydoc = profilescol.find(myquery)
  for x in mydoc:
    return x
  return False

def add_user(user_id, username):
  document = [{
    "_id": int(user_id),
    "Username": username,
    "Upvotes": 0,
    "Roles": [],
    "Posted": [],
    "NameColour": None,
    "BackgroundColour": None,
    "Warnings": 0
  }]
  profilescol.insert_many(document)

def add_role(user_id, role):
  user = get_user(user_id)
  if role not in user['Roles']:
    roles = user['Roles']
    roles.append(role)
    del user['Roles']
    user['Roles'] = roles
    profilescol.delete_one({"_id": user['_id']})
    profilescol.insert_many([user])

def get_scenario(theid):
  myquery = {"_id": int(theid)}
  mydoc = scol.find(myquery)
  for x in mydoc:
    return x
  return False

def get_nv_scenario(theid):
  myquery = {"_id": ObjectId(theid)}
  mydoc = nvscol.find(myquery)
  for x in mydoc:
    return x
  return False

def get_nv_scenario_user(user_id):
  myquery = {"UserId": user_id}
  mydoc = nvscol.find(myquery)
  all_nvs = []
  for x in mydoc:
    all_nvs.append(x)
  return all_nvs

def add_scenario(title, description, user_id):
  document = [{
    "Title": title,
    "Desc": description,
    "UserId": user_id
  }]
  nvscol.insert_many(document)
  return "This scenerio is now waiting for verification!"

def decline_scenario(theid):
  scenario = get_nv_scenario(theid)
  if scenario == False:
    return "This scenario doesn't exist!"
  nvscol.delete_one({"_id": scenario['_id']})
  return "The scenario has been declined!"

def accept_scenario(theid):
  scenario = get_nv_scenario(theid)
  user_id = scenario['UserId']
  if scenario == False:
    return "This scenario doesn't exist!"
  highest_id = get_max_id()
  document = [{
    "_id": highest_id + 1,
    "Title": scenario['Title'],
    "Desc": scenario['Desc']
  }]
  nvscol.delete_one({"_id": scenario['_id']})
  scol.insert_many(document)
  add_role(user_id, "Helper")
  return "This scenario has been accepted!"

def url_encode(text):
  return urllib.parse.quote(text)

def get_all_nvs():
  scenarios = []
  for scenario in nvscol.find():
    scenarios.append(scenario)
  return scenarios

def get_all_scenarios():
  scenarios = []
  for scenario in scol.find():
    scenarios.append(scenario)
  return scenarios

def get_max_id():
  mydoc = scol.find().sort("_id", -1).limit(1)
  highest_id = 0
  for x in mydoc:
    highest_id = x['_id']
  return highest_id

def get_all_comments(theid):
  comments = []
  myquery = {"Post": int(theid)}
  mydoc = ccol.find(myquery)
  for x in mydoc:
    comments.append(x)
  return comments

def post_comment(postid, comment, userid, username):
  user = get_user(userid)
  scenario = get_scenario(postid)
  if scenario == False:
    return f"{postid} is not a real scenario id!"
  if postid in user['Posted']:
    return f"You have already commented on {scenario['Title']}"
  if len(comment) > 300:
    return "Your thoughts have to be less than 100 characters"
  comment = censor(comment)
  document = [{
    "Post": int(postid),
    "UserId": int(userid),
    "Username": username,
    "Body": comment
  }]
  ccol.insert_many(document)
  posted = user['Posted']
  posted.append(int(postid))
  del user['Posted']
  user['Posted'] = posted
  profilescol.delete_one({"_id": user['_id']})
  profilescol.insert_many([user])
  return True

def edit_scenario(postid, title, desc):
  scenario = get_scenario(postid)
  if scenario == False:
    return "That is not a real scenario!"
  del scenario['Desc']
  scenario['Desc'] = desc
  del scenario['Title']
  scenario['Title'] = title
  scol.delete_one({"_id": scenario['_id']})
  scol.insert_many([scenario])
  return True

def get_comment(username, postid):
  myquery = {"Username": username, "Post": int(postid)}
  mydoc = ccol.find(myquery)
  for x in mydoc:
    return x
  return False

def delete_comment(username, postid):
  comment = get_comment(username, postid)
  if comment == False:
    return "That is not a real comment!"
  ccol.delete_one({"_id": comment['_id']})
  return True

def get_comments_user(username):
  myquery = {"Username": username}
  mydoc = ccol.find(myquery)
  comments = []
  for x in mydoc:
    comments.append(x)
  return comments

def get_nvs_user(userid):
  myquery = {"UserId": str(userid)}
  mydoc = nvscol.find(myquery)
  comments = []
  for x in mydoc:
    comments.append(x)
  return comments

def ban_user(username, reason):
  if get_user_from_username(username) == False:
    return f"{username} is not a real username! Make sure to be case sensitive!"
  # delete all comments
  comments = get_comments_user(username)
  for comment in comments:
    delete = {"_id": comment['_id']}
    ccol.delete_one(delete)
  # add banned to user
  user = get_user_from_username(username)
  userid = user['_id']
  user['Banned'] = reason
  profilescol.delete_one({"_id": user['_id']})
  profilescol.insert_many([user])
  # delete all unverified scenarios
  nvs = get_nvs_user(userid)
  for nv in nvs:
    delete = {"_id": nv['_id']}
    nvscol.delete_one({"_id": nv['_id']})
  return True

def unban_user(username):
  if get_user_from_username(username) == False:
    return f"{username} is not a real username! Make sure to be case sensitive!"
  user = get_user_from_username(username)
  del user['Banned']
  profilescol.delete_one({"_id": user['_id']})
  profilescol.insert_many([user])

def add_warning(username, amount):
  if get_user_from_username(username) == False:
    return f"{username} is not a real username! Make sure to be case sensitive!"
  user = get_user_from_username(username)
  warnings = user['Warnings']
  warnings = warnings + int(amount)
  del user['Warnings']
  user['Warnings'] = warnings
  profilescol.delete_one({"Username": username})
  profilescol.insert_many([user])
  return True

def censor(word):
  new_word = profanity.censor(word)
  return new_word

def if_user_follows(username):
  data = requests.post("https://firewalledreplit.com/graphql", json = {
  			"query": """
  query userByUsername($username: String!) {
  	userByUsername(username: $username) {
      isFollowingCurrentUser
    }
  }
     """,
  			"variables": """{ "username": "%s" }""" % username
  		},
  headers = {
    "X-Requested-With": "ReplitApi",
    "referer": "https://replit.com/",
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"connect.sid={os.getenv('cookie')}"
  })
  data = json.loads(data.text)["data"]["userByUsername"]
  return data['isFollowingCurrentUser']

def profile_pic(username):
  data = requests.post("https://firewalledreplit.com/graphql", json = {
  			"query": """
  query userByUsername($username: String!) {
  	userByUsername(username: $username) {
      image
    }
  }
     """,
  			"variables": """{ "username": "%s" }""" % username
  		},
  headers = {
    "X-Requested-With": "ReplitApi",
    "referer": "https://replit.com/",
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"connect.sid={os.getenv('cookie')}"
  })
  data = json.loads(data.text)["data"]["userByUsername"]
  return data['image']