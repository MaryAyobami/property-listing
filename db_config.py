import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        user="ivantageAdmin",
        password="ivantagedb",
        database="radius_v2",
        host="34.228.134.49"
    )
