import csv
import pymysql
import getpass
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'oracle'
DB_NAME = 'attendance_db'

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def authenticate(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username=%s', (username,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0] == password:
        return True
    return False

def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
        conn.commit()
        print("User registered successfully!")
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_user():
    username = input("New Username: ")
    password = getpass.getpass("New Password: ")
    register_user(username, password)

def add_attendance(name, date, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT student_id FROM students WHERE name=%s', (name,))
    result = cursor.fetchone()
    if result:
        student_id = result[0]
    else:
        cursor.execute('INSERT INTO students (name) VALUES (%s)', (name,))
        student_id = cursor.lastrowid
    cursor.execute('INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)', 
                   (student_id, date, status))
    conn.commit()
    conn.close()

from datetime import datetime

def import_attendance_from_csv(file_path):
    required_columns = {'name', 'date', 'status'}
    
    # Remove any surrounding quotes from the file path
    file_path = file_path.strip('"\'')

    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            if not required_columns.issubset(reader.fieldnames):
                raise KeyError(f"CSV file must contain columns: {required_columns}")

            conn = get_db_connection()
            cursor = conn.cursor()
            
            for row in reader:
                name = row['name']
                # Convert date from DD-MM-YYYY to YYYY-MM-DD
                try:
                    date = datetime.strptime(row['date'], '%d-%m-%Y').strftime('%Y-%m-%d')
                except ValueError as ve:
                    print(f"Date conversion error: {ve} for row: {row}")
                    continue
                status = row['status']
                
                cursor.execute('SELECT student_id FROM students WHERE name=%s', (name,))
                result = cursor.fetchone()
                if result:
                    student_id = result[0]
                else:
                    cursor.execute('INSERT INTO students (name) VALUES (%s)', (name,))
                    student_id = cursor.lastrowid
                cursor.execute('INSERT INTO attendance (student_id, date, status) VALUES (%s, %s, %s)', 
                               (student_id, date, status))
            
            conn.commit()
            conn.close()
            print("Attendance data imported successfully.")
    except Exception as e:
        print(f"Failed to import CSV: {e}")
1

def generate_report():
    conn = get_db_connection()
    df = pd.read_sql('''
    SELECT s.name, a.date, a.status
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    ''', conn)
    conn.close()

    # Generate a simple attendance report
    report_file = 'attendance_report.csv'
    df.to_csv(report_file, index=False)
    print(f"Report generated: {report_file}")

    # Plot attendance count per student
    plt.figure(1)
    sns.countplot(x='name', hue='status', data=df)
    plt.title('Attendance Count per Student')
    plt.xlabel('Student Name')
    plt.ylabel('Count')
    plt.legend(title='Status')
    plt.xticks(rotation=45)
    plt.savefig('attendance_count.png')
    print("Graph saved as attendance_count.png")

    # Plot attendance over time
    plt.figure(2)
    df['date'] = pd.to_datetime(df['date'])
    attendance_over_time = df.groupby(['date', 'status']).size().reset_index(name='count')
    sns.lineplot(x='date', y='count', hue='status', data=attendance_over_time)
    plt.title('Attendance Over Time')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.legend(title='Status')
    plt.savefig('attendance_over_time.png')
    print("Graph saved as attendance_over_time.png")

def main():
    print("Welcome to the Attendance Management System")

    while True:
        print("\nOptions:")
        print("1. Login")
        print("2. Register")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Username: ")
            password = getpass.getpass("Password: ")

            if authenticate(username, password):
                print("Login successful!")
                # User is authenticated, proceed with application logic
                while True:
                    print("\nOptions:")
                    print("1. Add Attendance")
                    print("2. Import Attendance from CSV")
                    print("3. Generate Report")
                    print("4. Logout")

                    choice = input("Enter your choice: ")

                    if choice == '1':
                        name = input("Student Name: ")
                        date = input("Date (YYYY-MM-DD): ")
                        status = input("Status (Present/Absent): ")
                        add_attendance(name, date, status)
                        print("Attendance record added successfully.")

                    elif choice == '2':
                        file_path = input("Enter the full path to the CSV file (including file name): ")
                        try:
                            import_attendance_from_csv(file_path)
                            print("Attendance data imported successfully.")
                        except Exception as e:
                            print(f"Failed to import CSV: {e}")

                    elif choice == '3':
                        generate_report()

                    elif choice == '4':
                        print("Logging out.")
                        break

                    else:
                        print("Invalid choice. Please try again.")
            else:
                print("Invalid username or password.")

        elif choice == '2':
            add_user()

        elif choice == '3':
            print("Exiting the system.")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
