import mysql.connector
from datetime import datetime

class ChatDatabase:
    def connect_db(self):
        try:
            # Establish a new connection to the database
            connection = mysql.connector.connect(
                host='localhost',
                user='rio',
                password='jj123!@#',
                database='chat_history'
            )
            print("Database connection established successfully.")
            return connection
        except mysql.connector.Error as err:
            print(f"Error connecting to database: {err}")
            return None

    def query_database(self, msg):
        connection = self.connect_db()
        if connection:
            cursor = connection.cursor()
            try:
                search_query = """
                    SELECT user, bot, timestamp
                    FROM conversation
                    WHERE LOWER(user) = LOWER(%s)
                    ORDER BY timestamp DESC
                """
                cursor.execute(search_query, (msg,))
                search_results = cursor.fetchall()

                if search_results:
                    return search_results[0][1]
                else:
                    return ""
            except mysql.connector.Error as err:
                print(f"Error: {err}")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Failed to connect to the database")

    def insert_data(self, user_input, bot_response):
        connection = self.connect_db()
        if connection:
            cursor = connection.cursor()
            try:
                insert_query = """
                    INSERT INTO conversation (user, bot, timestamp)
                    VALUES (%s, %s, %s)
                """
                current_time = datetime.now()
                cursor.execute(insert_query, (user_input, bot_response, current_time))
                connection.commit() 
                print(f"Data inserted successfully:")
            except mysql.connector.Error as err:
                print(f"Error: {err}")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Failed to connect to the database")
