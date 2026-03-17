# setup_db.py

import mysql.connector
from mysql.connector import Error

def create_database():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='your_mysql_password'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS campus_stationery_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("Database 'campus_stationery_db' created successfully!")
            
            # Create user with privileges (optional)
            cursor.execute("CREATE USER IF NOT EXISTS 'campus_user'@'localhost' IDENTIFIED BY 'strong_password'")
            cursor.execute("GRANT ALL PRIVILEGES ON campus_stationery_db.* TO 'campus_user'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print("Database user created and privileges granted!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_database()