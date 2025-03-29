import mysql.connector
import random
import string

def create_database():
    # Connect to MySQL server (no database selected yet)
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",           # Default phpMyAdmin user, change if needed
            password=""            # Default empty password, change if needed
        )
        
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS flask_company_system")
        cursor.execute("USE flask_company_system")
        
        print("Database created successfully!")
        
        # Create company table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id VARCHAR(10) UNIQUE NOT NULL,
            company_name VARCHAR(100) NOT NULL,
            company_email VARCHAR(100) UNIQUE NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(100)
        )
        """)
        
        # Create developer table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS developer (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id VARCHAR(10) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(100),
            FOREIGN KEY (company_id) REFERENCES company(company_id),
            CONSTRAINT unique_company_developer UNIQUE (company_id)
        )
        """)
        
        # Create user table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id VARCHAR(10) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_verified BOOLEAN DEFAULT FALSE,
            verification_token VARCHAR(100),
            FOREIGN KEY (company_id) REFERENCES company(company_id)
        )
        """)
        
        print("All tables created successfully!")
        
        # Function to generate a unique company ID starting with CCP
        def generate_company_id():
            while True:
                # Generate a random 7-digit number
                random_digits = ''.join(random.choices(string.digits, k=7))
                # Combine with CCP prefix
                company_id = f"CCP{random_digits}"
                
                # Check if it exists in the database
                cursor.execute("SELECT COUNT(*) FROM company WHERE company_id = %s", (company_id,))
                count = cursor.fetchone()[0]
                
                if count == 0:
                    return company_id
        
        # Add sample company for testing (optional)
        add_sample = input("Do you want to add a sample company for testing? (y/n): ")
        if add_sample.lower() == 'y':
            company_id = generate_company_id()
            cursor.execute("""
            INSERT INTO company (company_id, company_name, company_email, email_verified)
            VALUES (%s, %s, %s, %s)
            """, (company_id, "Test Company", "test@company.com", True))
            
            print(f"Sample company created with ID: {company_id}")
            
            # Add sample developer
            add_dev = input("Add a sample developer for this company? (y/n): ")
            if add_dev.lower() == 'y':
                cursor.execute("""
                INSERT INTO developer (company_id, email, password, email_verified)
                VALUES (%s, %s, %s, %s)
                """, (company_id, "dev@test.com", "hashed_password_here", True))
                print("Sample developer added")
            
            # Add sample user
            add_user = input("Add a sample user for this company? (y/n): ")
            if add_user.lower() == 'y':
                cursor.execute("""
                INSERT INTO user (company_id, email, password, email_verified)
                VALUES (%s, %s, %s, %s)
                """, (company_id, "user@test.com", "hashed_password_here", True))
                print("Sample user added")
        
        conn.commit()
        print("Database setup complete!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    print("Creating database for Company Registration System...")
    create_database() 