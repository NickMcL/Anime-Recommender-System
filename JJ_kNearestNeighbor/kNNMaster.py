import numpy as np
import sqlite3 as sql
import math


####################### Functions to grab data ################################

def getUsers(cursor):
    print("Getting users:")

    #grabs the list of users from the database
    cursor.execute('SELECT DISTINCT user_name FROM MALUserScores ORDER BY user_name ASC')

    #makes the list of users out of the grabbed info
    userList = cursor.fetchall()
    
    userIndex = np.arange(len(userList)).reshape(1, len(userList))
    userNames = np.asarray(userList)[:, 0]
    
    #row 0: user index
    #row 1: user name
    #userIndexList = np.vstack([userIndex, userNames])

    return np.vstack([userIndex, userNames])


def getAnimeList(cursor):
    print("Getting anime list:")

    #grabs the list of anime from the database
    cursor.execute('SELECT DISTINCT anime_name FROM MALRatingsTrain ORDER BY anime_name ASC')

    #makes the list of anime out of the grabbed info
    #animeList[0][0] = first anime name
    #animeList[1][0] = second anime name
    animeList = cursor.fetchall()
    
    animeIndex = np.arange(len(animeList)).reshape(1, len(animeList))
    animeNames = np.asarray(animeList)[:, 0]

    #row 0: anime index  #animeIndexList[0][0] #index
    #row 1: anime name   #animeIndexList[1][0] #anime name
    #animeIndexList = np.vstack([animeIndex, animeNames])

    return np.vstack([animeIndex, animeNames])


def getUserScores(cursor, userIndexList, animeIndexList):
    print("Getting user scores:")

    #tells us how many users and anime there are
    numAnimes = len(animeIndexList[1, :])
    numUsers = len(userIndexList[1, :])

    #Initialize the userScores matrix with zeros
    userScores = np.zeros((len(animeIndexList[1,:]), len(userIndexList[1,:])))
    
    #index used when going through userScores matrix
    userIndex = 0

    #adds each users data to the userScores matrix
    for user in userIndexList[1, :]:
        #replaces the single and double quotes in the user name with esc chars
        user = user.replace("\'","\'\'").replace("\"","\"\"")

        #build the SQL query to grab this user's rating of this show
        query = "SELECT anime_name, score FROM MALUserScores WHERE user_name = '"
        query += user
        query += "'"

        #sends the query to the DB to grab the user scores for current single user
        cursor.execute(query)

        #puts the data into userRatings
        userRatings = cursor.fetchall()
	
        #sorts the the user's rating data into the userScores matrix
        for animeScoreTuple in userRatings:
            #searches animeIndexList for the index of the anime
            #name contained in animeScoreTuple[0]
            animeIndex = np.searchsorted(animeIndexList[1,:], animeScoreTuple[0])
        
            #sets the score into the userScores matrix for current user and anime
            userScores[animeIndex,userIndex] = animeScoreTuple[1]
        
        userIndex += 1

    return userScores


#TODO could edit to return invIndex (currently only returns user scores)
def makeInvIndex(cursor):
    print("Making inverted index:")
    
    #grabs the list of anime
    animeIndexList = getAnimeList(cursor)

    #grabs the list of user names
    userIndexList = getUsers(cursor)
        
    #grabs the users scores
    scoreMatrix = getUserScores(cursor, userIndexList, animeIndexList)

    return animeIndexList, userIndexList, scoresMatrix

########################## Functions for kNN ##################################

#creates a matrix of 1s and 0s, where each element is
#1 if user has watched show (not neccessarily rated),
#and 0 otherwise.
def watchedMatrix(cursor, userScores, numAnime, numUsers):
    print("Calculating the watched matrix:")
    #size of watched matrix being created with 0s input
    userWatched = np.zeros(userScoreIndex.shape)
    #goes through and fills a 1 for anime users have watched
    for i in range(0,numAnime):
	    for j in range(0,numUsers):
		    if (userScores[i,j] != 0):
			    userWatched[i,j] = 1


def kNN(cursor, animeIndexList, userIndexList, userScores, userWatchedList)
    print("Calculating kNN for input user")
    #calculates the number of anime and users
    numAnime = len(userIndexList[1, :])
    numUsers = len(animeIndexList[1, :])


def main():
    print("Starting kNN Anime Recommender:")
    
    #grabs the database of user info (their anime scores)
    con = sql.connect('../small_rating_sets.db')
    cursor = con.cursor()

    #creates the user score index matrix
    animeIndexList, userIndexList, userScores = makeInvIndex(cursor)

    #calculates the number of anime and users
    numAnime = len(userIndexList[1, :])
    numUsers = len(animeIndexList[1, :])

    #calculate the watched matrix for all the users
    userWatched = watchedMatrix(cursor, userScores, numAnime, numUsers)

    kNNList = kNN(cursor, animeIndexList, userIndexList, userScores, userWatched)


if __name__ == '__main__':
    main()
