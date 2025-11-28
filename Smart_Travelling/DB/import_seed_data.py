"""
Script to import seed data from CSV files to MySQL database
Handles places and addresses tables with proper foreign key relationships
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error
import re
import os
from typing import Optional, Tuple
import unicodedata

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'phu123456789@',
    'database': 'smart_tourism'
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        # First, connect without specifying database to create it if needed
        config_no_db = DB_CONFIG.copy()
        database_name = config_no_db.pop('database')
        
        connection = mysql.connector.connect(**config_no_db)
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ Database '{database_name}' is ready")
        
        cursor.close()
        connection.close()
        
        # Now connect to the database
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print(f"✓ Connected to MySQL database: {DB_CONFIG['database']}")
            return connection
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        return None

def clean_price(price_str) -> Optional[int]:
    """Convert price string to integer (remove VND, commas, dots)"""
    if pd.isna(price_str) or price_str == 'NULL':
        return None
    
    # Remove all non-digit characters
    price_clean = re.sub(r'[^\d]', '', str(price_str))
    
    if price_clean:
        return int(price_clean)
    return None

def clean_time(time_str) -> Optional[str]:
    """Convert time to HH:MM format"""
    if pd.isna(time_str) or time_str == 'NULL' or time_str == 'None':
        return None
    
    time_str = str(time_str).strip()
    
    # If already in HH:MM format
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        parts = time_str.split(':')
        return f"{int(parts[0]):02d}:{parts[1]}"
    
    # If in H:MM or HH:MM format
    if ':' in time_str:
        parts = time_str.split(':')
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    
    return None

def clean_phone(phone_str) -> Optional[str]:
    """Clean phone number"""
    if pd.isna(phone_str) or phone_str == 'NULL' or phone_str == 'None':
        return None
    
    phone_clean = str(phone_str).strip()
    if phone_clean and phone_clean != 'N/A':
        return phone_clean
    return None

def clean_coordinates(lat_str, lng_str) -> Tuple[Optional[float], Optional[float]]:
    """Extract and clean latitude and longitude"""
    lat, lng = None, None
    
    # Handle combined coordinate string (e.g., "lat, lng")
    if pd.notna(lat_str) and isinstance(lat_str, str) and ',' in lat_str:
        coords = lat_str.split(',')
        if len(coords) == 2:
            try:
                lat = float(coords[0].strip())
                lng = float(coords[1].strip())
                return lat, lng
            except ValueError:
                pass
    
    # Handle separate lat/lng
    try:
        if pd.notna(lat_str) and lat_str != 'NULL':
            lat = float(str(lat_str).strip())
    except (ValueError, AttributeError):
        lat = None
    
    try:
        if pd.notna(lng_str) and lng_str != 'NULL':
            lng = float(str(lng_str).strip())
    except (ValueError, AttributeError):
        lng = None
    
    return lat, lng

def clean_string(value) -> Optional[str]:
    """Clean string values"""
    if pd.isna(value) or value == 'NULL' or value == 'None' or value == 'N/A':
        return None
    
    return str(value).strip() if value else None

def normalize_name(name: str) -> str:
    """Normalize Vietnamese name for search"""
    # Convert to lowercase
    name = name.lower()
    
    # Remove Vietnamese accents
    name = unicodedata.normalize('NFD', name)
    name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
    
    # Remove special characters, keep only alphanumeric and spaces
    name = re.sub(r'[^\w\s]', ' ', name)
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    return name

def insert_address(cursor, data: dict) -> Optional[int]:
    """Insert address and return its ID"""
    query = """
    INSERT INTO addresses (house_number, street, ward, district, city, lat, lng, url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = (
        data.get('house_number'),
        data.get('street'),
        data.get('ward'),
        data.get('district'),
        data.get('city'),
        data.get('lat'),
        data.get('lng'),
        data.get('url')
    )
    
    try:
        cursor.execute(query, values)
        return cursor.lastrowid
    except Error as e:
        print(f"✗ Error inserting address: {e}")
        return None

def insert_place(cursor, data: dict) -> Optional[int]:
    """Insert place and return its ID"""
    query = """
    INSERT INTO places (
        name, normalized_name, price_vnd, summary, description,
        open_time, close_time, phone, rating, review_count,
        popularity, category, dwell, image_name, image_url,
        tags, address_id
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s
    )
    """
    
    values = (
        data.get('name'),
        normalize_name(data.get('name', '')),
        data.get('price_vnd'),
        data.get('summary'),
        data.get('description'),
        data.get('open_time'),
        data.get('close_time'),
        data.get('phone'),
        data.get('rating'),
        data.get('review_count'),
        data.get('popularity'),
        data.get('category'),
        data.get('dwell'),
        data.get('image_name'),
        data.get('image_url'),
        data.get('tags'),
        data.get('address_id')
    )
    
    try:
        cursor.execute(query, values)
        return cursor.lastrowid
    except Error as e:
        print(f"✗ Error inserting place '{data.get('name')}': {e}")
        return None

def import_mien_bac(connection, csv_path: str):
    """Import data from Mien Bac CSV"""
    print(f"\n📂 Importing Mien Bac data from: {csv_path}")
    
    df = pd.read_csv(csv_path)
    cursor = connection.cursor()
    
    success_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        try:
            # Extract coordinates
            lat, lng = clean_coordinates(row.get('lat'), row.get('long'))
            
            # Insert address
            address_data = {
                'house_number': clean_string(row.get('houseNumber')),
                'street': clean_string(row.get('street')),
                'ward': clean_string(row.get('ward')),
                'district': clean_string(row.get('district')),
                'city': clean_string(row.get('city')),
                'lat': lat,
                'lng': lng,
                'url': clean_string(row.get('link g gmap'))
            }
            
            address_id = insert_address(cursor, address_data)
            
            if address_id:
                # Insert place
                place_data = {
                    'name': clean_string(row.get('Địa điểm')),
                    'price_vnd': clean_price(row.get('Giá tham khảo')),
                    'summary': clean_string(row.get('Sumary')),
                    'description': clean_string(row.get('Description')),
                    'open_time': clean_time(row.get('Giờ Mở Cửa ')),
                    'close_time': clean_time(row.get('Giờ Đóng Cửa ')),
                    'phone': clean_phone(row.get('Phone')),
                    'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else None,
                    'review_count': int(row['Reviewcount']) if pd.notna(row.get('Reviewcount')) else 0,
                    'popularity': int(row['Popularity']) if pd.notna(row.get('Popularity')) and row.get('Popularity') != 'None' else None,
                    'category': None,
                    'dwell': None,
                    'image_name': clean_string(row.get('Img name')),
                    'image_url': clean_string(row.get('Img url')),
                    'tags': None,
                    'address_id': address_id
                }
                
                place_id = insert_place(cursor, place_data)
                
                if place_id:
                    success_count += 1
                    print(f"✓ [{success_count}] Imported: {place_data['name']}")
                else:
                    error_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"✗ Error processing row {index}: {e}")
    
    connection.commit()
    cursor.close()
    
    print(f"\n📊 Mien Bac: {success_count} success, {error_count} errors")
    return success_count, error_count

def import_mien_nam(connection, csv_path: str):
    """Import data from Mien Nam CSV"""
    print(f"\n📂 Importing Mien Nam data from: {csv_path}")
    
    df = pd.read_csv(csv_path)
    cursor = connection.cursor()
    
    success_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        try:
            # Extract coordinates from "Tọa độ" column (format: "lat, lng")
            coords_str = clean_string(row.get('Tọa độ'))
            lat, lng = clean_coordinates(coords_str, None)
            
            # Insert address
            address_data = {
                'house_number': clean_string(row.get('Số nhà')),
                'street': clean_string(row.get('Đường')),
                'ward': clean_string(row.get('Phường/Xã')),
                'district': clean_string(row.get('Quận/Huyện')),
                'city': clean_string(row.get('T.Phố')),
                'lat': lat,
                'lng': lng,
                'url': clean_string(row.get('URL'))
            }
            
            address_id = insert_address(cursor, address_data)
            
            if address_id:
                # Insert place
                place_data = {
                    'name': clean_string(row.get('Tên địa điểm')),
                    'price_vnd': clean_price(row.get('Giá vé (VNĐ)')),
                    'summary': None,
                    'description': None,
                    'open_time': clean_time(row.get('Giờ mở')),
                    'close_time': clean_time(row.get('Giờ đóng')),
                    'phone': clean_phone(row.get('Phone')),
                    'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else None,
                    'review_count': int(row['Review Count']) if pd.notna(row.get('Review Count')) else 0,
                    'popularity': None,
                    'category': clean_string(row.get('Loại hình')),
                    'dwell': None,
                    'image_name': None,
                    'image_url': None,
                    'tags': None,
                    'address_id': address_id
                }
                
                place_id = insert_place(cursor, place_data)
                
                if place_id:
                    success_count += 1
                    print(f"✓ [{success_count}] Imported: {place_data['name']}")
                else:
                    error_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"✗ Error processing row {index}: {e}")
    
    connection.commit()
    cursor.close()
    
    print(f"\n📊 Mien Nam: {success_count} success, {error_count} errors")
    return success_count, error_count

def import_mien_trung(connection, csv_path: str):
    """Import data from Mien Trung CSV"""
    print(f"\n📂 Importing Mien Trung data from: {csv_path}")
    
    df = pd.read_csv(csv_path)
    cursor = connection.cursor()
    
    success_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row.get('Địa điểm')) or not str(row.get('Địa điểm')).strip():
            continue
            
        try:
            # Extract coordinates from "coordinates" column (format: "lat - lng")
            coords_str = clean_string(row.get('coordinates'))
            lat, lng = None, None
            
            if coords_str and '-' in coords_str:
                coords = coords_str.split('-')
                if len(coords) == 2:
                    try:
                        lat = float(coords[0].strip())
                        lng = float(coords[1].strip())
                    except ValueError:
                        pass
            
            # Insert address
            address_data = {
                'house_number': None,
                'street': clean_string(row.get('street')),
                'ward': clean_string(row.get('ward')),
                'district': clean_string(row.get('district')),
                'city': clean_string(row.get('city')),
                'lat': lat,
                'lng': lng,
                'url': clean_string(row.get('link g gmap'))
            }
            
            address_id = insert_address(cursor, address_data)
            
            if address_id:
                # Insert place
                place_data = {
                    'name': clean_string(row.get('Địa điểm')),
                    'price_vnd': clean_price(row.get('Giá tham khảo')),
                    'summary': clean_string(row.get('Sumary')),
                    'description': clean_string(row.get('Description')),
                    'open_time': clean_time(row.get('Giờ Mở Cửa')),
                    'close_time': clean_time(row.get('Giờ Đóng Cửa')),
                    'phone': clean_phone(row.get('Phone')),
                    'rating': float(row['Rating']) if pd.notna(row.get('Rating')) else None,
                    'review_count': int(str(row['Reviewcount']).replace(',', '')) if pd.notna(row.get('Reviewcount')) else 0,
                    'popularity': None,
                    'category': None,
                    'dwell': None,
                    'image_name': clean_string(row.get('Img name')),
                    'image_url': None,
                    'tags': None,
                    'address_id': address_id
                }
                
                place_id = insert_place(cursor, place_data)
                
                if place_id:
                    success_count += 1
                    print(f"✓ [{success_count}] Imported: {place_data['name']}")
                else:
                    error_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            error_count += 1
            print(f"✗ Error processing row {index}: {e}")
    
    connection.commit()
    cursor.close()
    
    print(f"\n📊 Mien Trung: {success_count} success, {error_count} errors")
    return success_count, error_count

def create_tables(connection):
    """Create database tables from SQL files"""
    print("\n📋 Creating database tables...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_files = [
        '1_addresses.sql',
        '2_places.sql'
    ]
    
    cursor = connection.cursor()
    
    for sql_file in sql_files:
        sql_path = os.path.join(current_dir, sql_file)
        if os.path.exists(sql_path):
            try:
                with open(sql_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    
                    # Split by semicolon and execute each statement
                    statements = sql_content.split(';')
                    for statement in statements:
                        statement = statement.strip()
                        if statement:
                            cursor.execute(statement)
                
                print(f"✓ Executed: {sql_file}")
            except Error as e:
                print(f"✗ Error executing {sql_file}: {e}")
        else:
            print(f"⚠ Warning: {sql_file} not found")
    
    connection.commit()
    cursor.close()
    print("✓ Tables created successfully\n")

def main():
    """Main function to import all CSV files"""
    print("=" * 60)
    print("🚀 Starting seed data import to MySQL")
    print("=" * 60)
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # CSV file paths
    csv_files = {
        'Mien Bac': os.path.join(current_dir, 'seed_MienBac.csv'),
        'Mien Nam': os.path.join(current_dir, 'seed_MienNam.csv'),
        'Mien Trung': os.path.join(current_dir, 'seed_MienTrung.csv')
    }
    
    # Check if files exist
    for region, path in csv_files.items():
        if not os.path.exists(path):
            print(f"✗ Error: {region} CSV file not found at: {path}")
            return
    
    # Connect to database
    connection = get_db_connection()
    
    if not connection:
        print("✗ Failed to connect to database. Please check your DB_CONFIG settings.")
        return
    
    # Create tables first
    create_tables(connection)
    
    try:
        total_success = 0
        total_error = 0
        
        # Import each region
        success, error = import_mien_bac(connection, csv_files['Mien Bac'])
        total_success += success
        total_error += error
        
        success, error = import_mien_nam(connection, csv_files['Mien Nam'])
        total_success += success
        total_error += error
        
        success, error = import_mien_trung(connection, csv_files['Mien Trung'])
        total_success += success
        total_error += error
        
        print("\n" + "=" * 60)
        print(f"✅ Import completed!")
        print(f"📊 Total: {total_success} places imported successfully")
        print(f"📊 Total: {total_error} errors")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
    
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n🔌 Database connection closed")

if __name__ == "__main__":
    main()