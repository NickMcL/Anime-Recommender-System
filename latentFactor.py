import sqlite3 as lite
import numpy as np
import sys


con = lite.connect('data_acq/mal_users.db')

with con:    

    userList = []
    animeList = []

    con.text_factory = str
    cur = con.cursor()   
    cur.execute("SELECT DISTINCT user_name FROM MALUserScores ORDER BY user_name ASC")
    users = cur.fetchall()
    for user in users:
        userList.append(user[0])

    con.text_factory = str
    cur = con.cursor()   
    cur.execute("SELECT DISTINCT anime_name FROM MALUserScores ORDER BY user_name ASC")
    animes = cur.fetchall()
    for anime in animes:
        animeList.append(anime[0])

    # print animeList[0][0]

    totUser = len(userList)
    totAnime = len(animeList)

    # print totUser
    # print totAnime

    matrix = np.zeros((totUser,totAnime))

    cur = con.cursor()   
    cur.execute("SELECT * FROM MALUserScores")
    rows = cur.fetchall()
    for row in rows:
        matrix[userList.index(row[0])][animeList.index(row[1])] = row[3]

    print matrix


# N = totUser/2

# A = np.ones((totUser, N))
# B = np.ones((N, totAnime))

# print A

#     w = zeros(1,4);
#     b = 0;

#     C = 5;
#     N = 76;

#     for i = 1:1000
#         sumW = zeros(1,4);
#         sumB = 0;
#         for j = 1:N
#             if(q3t_train(j) .* (w * transpose(q3x_train(j,:)) + b) < ones(1,4))
#                 wGrad = w./N - (C .* q3t_train(j) .* q3x_train(j,:));
#                 bGrad = -q3t_train(j);
#             else
#                 wGrad = w./N;
#                 bGrad = 0;
#             end

#             alpha = 0.5 / (1 + i*0.5);
#             w = w - (alpha .* wGrad);
#             b = b - ((0.01 * alpha) .* bGrad);

#         end


#     end


#     y = zeros(1,24);
#     y = w * transpose(q3x_test) + b;
#     y = transpose(y);

#     for k = 1:24
#         if y(k) > 0
#             y(k) = 1;
#         else
#             y(k) = 0;
#         end

#         if q3t_test(k) < 0
#             q3t_test(k) = 0;
#         end
#     end

#     error = nnz(xor(y,q3t_test)) / 24 * 100
    
# end