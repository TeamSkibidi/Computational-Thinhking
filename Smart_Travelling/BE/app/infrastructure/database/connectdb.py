import mysql.connector
from mysql.connector import Error

def get_db():
    
    try:
        connection = mysql.connector.connect( host="localhost", user="root", password="Minh12345678!", database="travel")
        return connection
    except Error as e:
        print("Lỗi kết nối MySQL:", e)
        return None


