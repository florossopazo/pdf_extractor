from .module.database_handler import get_db_connection

def test_connection():
    """j"""
    try:
        conn = get_db_connection()
        print("Successfully connected to MySQL!")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()