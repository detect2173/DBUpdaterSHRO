import mysql.connector
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox


def choose_csv_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    return file_path


def get_students_from_db(database_connection, table_name):
    cursor = database_connection.cursor()
    cursor.execute(f"SELECT StudentID, Firstname, Lastname FROM {table_name}")

    students = {row[0]: f"{row[1]} {row[2]}" for row in cursor.fetchall()}

    cursor.close()
    return students


def get_students_from_csv(data):
    students = {}
    for _, row in data.iterrows():
        full_name = row['Name']
        if ', ' in full_name:
            last_name, first_name = full_name.split(', ')
        else:
            first_name, last_name = 'Unknown', full_name
        students[row['StudentID']] = f"{first_name} {last_name}"
    return students


def update_incentive(database_connection, table_name, data):
    cursor = database_connection.cursor()

    for index, row in data.iterrows():
        student_id = row['StudentID']
        incentive_value = row['Incentive']
        sql_query = f"UPDATE {table_name} SET Incentive = %s WHERE StudentID = %s"
        cursor.execute(sql_query, (incentive_value, student_id))

    database_connection.commit()
    cursor.close()


csv_file = choose_csv_file()
# Update the 'usecols' and 'names' parameters to match the correct column names in the CSV file
data = pd.read_csv(csv_file, usecols=['StudId', 'StudName', 'IncGrpName'])
data.rename(columns={'StudId': 'StudentID', 'StudName': 'Name', 'IncGrpName': 'Incentive'}, inplace=True)

config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'roster',
    'raise_on_warnings': True
}

try:
    connection = mysql.connector.connect(**config)

    table_name = 'roster'
    db_students = get_students_from_db(connection, table_name)
    csv_students = get_students_from_csv(data)

    db_student_ids_set = set(db_students.keys())
    csv_student_ids_set = set(csv_students.keys())

    not_in_db = {id: csv_students[id] for id in csv_student_ids_set if id not in db_student_ids_set}
    not_in_csv = {id: db_students[id] for id in db_student_ids_set if id not in csv_student_ids_set}
    print("db_students:", db_students)
    print("csv_students:", csv_students)

    message = "Students that need to be ADDED to the database:\n"
    message += "\n".join(f"{id}: {not_in_db[id]}" for id in not_in_db) if not_in_db else "None"
    message += "\n\nStudents that need to be DELETED from the database:\n"
    message += "\n".join(f"{id}: {not_in_csv[id]}" for id in not_in_csv) if not_in_csv else "None"

    update_incentive(connection, table_name, data)
    message += "\n\nIncentive column updated successfully."

except mysql.connector.Error as e:
    message = f"Error: {e}"
finally:
    if connection.is_connected():
        connection.close()

root = tk.Tk()
root.withdraw()
messagebox.showinfo("Results", message)
