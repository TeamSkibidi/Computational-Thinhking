import mysql.connector

db = mysql.connector.connect(user='root', password='Minh12345678!', host='localhost', database="travel")

#query
code = 'create schema `travel`;'

#run
mycursor = db.cursor()
mycursor.execute(code)



