import numpy as np
import sqlite3 as sql
import math

con = sql.connect('../data_acq/mal_users.db')

cursor = con.cursor()

#grabs the list of anime from the database
cursor.execute('SELECT DISTINCT anime_name FROM MALUserScores ORDER BY anime_name ASC')

#grabs the anime list
animeList = cursor.fetchall()
a = np.arange(len(animeList)).reshape(1, len(animeList))
b = np.asarray(animeList)[:, 0]
animeIndexList = np.vstack([a, b])

#for anime in animeList:
	
#returns the first anime
#print(animeList[0][0]) #keep the second index as 0
#print(animeList[1][0])

cursor.execute('SELECT DISTINCT user_name FROM MALUserScores ORDER BY user_name ASC')

#grabs the user list
userList = cursor.fetchall()
a = np.arange(len(userList)).reshape(1, len(userList))
b = np.asarray(userList)[:, 0]
#[index;
# name]
userIndexList = np.vstack([a, b])

numAnimes = len(animeIndexList[1, :])
numUsers = len(userIndexList[1, :])

#print userIndexList
#Initialize the userScores matrix with zeros
userScores = np.zeros((len(animeIndexList[1,:]), len(userIndexList[1,:])))
userIndex = 0
for user in userIndexList[1, :]:
	user = user.replace("\'","\'\'").replace("\"","\"\"")
	print user
	#build the SQL query to grab this user's rating of this show
	query = "SELECT anime_name, score FROM MALUserScores WHERE user_name = '"
	query += user
	query += "'"
	
	#grabs the query from the DB	
	cursor.execute(query)
	userRatings = cursor.fetchall()
	
	#sorts the the user's rating data into the userScores matrix
	for animeScoreTuple in userRatings:
		animeIndex = np.searchsorted(animeIndexList[1,:], animeScoreTuple[0])
		userScores[animeIndex,userIndex] = animeScoreTuple[1]
		#print user
		#print animeScoreTuple[0]
		#print userScores[animeIndex, userIndex]
	userIndex += 1


#TODO just arbitrary for now (no input)
inputUser = userScores[:,7]

#part 1 of our kNN
#create a matrix of 1s and 0s, where each element is
#1 if user has watched this show, 0 otherwise
userWatched = np.zeros(userScores.shape)
for i in range(0,numAnimes):
	for j in range(0,numUsers):
		if (userScores[i,j] != 0):
			userWatched[i,j] = 1

#distance of users
userDistances = np.zeros((1, numUsers))
#TODO just arbitrary for now (no input)
inputUserWatched = userWatched[:,7]

#finds the distances of the users to the input user
for i in range(0,numUsers):
	distanceSum = 0;
	for j in range(0, numAnimes):
		if (inputUserWatched[j] == 1 and userWatched[j, i] == 0):
			distanceSum += 1
	userDistances[0, i] = distanceSum

#number of users we will be wanting to use that are closest to input
numFilteredUsers = numUsers / 10

#row of indices over row of distances
userDistanceIndexMatrix = np.vstack([userIndexList[0,:], userDistances[0,:]])
#TODO once inputUser is made into a input user instead of a user being used.
filteredUserIndices = (userDistanceIndexMatrix[1,:].argsort())[1:numFilteredUsers + 1]

#print filteredUserIndices

#creates empty matrix for the filtered normalized users scores
filteredNormalizedUserScores = np.zeros((numAnimes, numFilteredUsers))
filteredUserDistance = np.zeros(numFilteredUsers)

#TODO find way to normalize

for i in range(0, numFilteredUsers):
	#print userScores[:,filteredUserIndices[i]]
	#magnitude = np.linalg.norm(np.nan_to_num(userScores[:,filteredUserIndices[i]]))
	#filteredNormalizedUserScores[:, i] = userScores[:,filteredUserIndices[i]] / magnitude
	#print filteredNormalizedUserScores[:,i]
	#print "\n"
	filteredNormalizedUserScores[:, i] = userScores[:,filteredUserIndices[i]]
	numerator = 0
	denominator = 0
#	numShowsCompared = 0
	for j in range(0, numAnimes):
		if (np.nan_to_num(inputUser[j]) != 0 and np.nan_to_num(filteredNormalizedUserScores[j,i]) != 0):
			difference = abs(np.nan_to_num(filteredNormalizedUserScores[j,i]) - inputUser[j])
			numerator += difference
			denominator += (difference*difference)
#			numShowsCompared += 1
	denominator = math.sqrt(denominator)
	filteredUserDistance[i] = numerator/denominator	
	print filteredUserDistance[i]
numNearestNeighbors = numFilteredUsers / 5
filteredUserDistanceIndices = np.vstack([filteredUserIndices, filteredUserDistance])
kNearestNeighbors = (filteredUserDistanceIndices[1,:].argsort())[:numNearestNeighbors]
for i in range(0, numNearestNeighbors):
	kNearestNeighbors[i] = filteredUserIndices[kNearestNeighbors[i]]
print kNearestNeighbors 

#PART 3: Finding the next show to watch
	
