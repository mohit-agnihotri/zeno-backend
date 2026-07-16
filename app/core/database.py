import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

if not url or not key:
    print("Warning: Supabase credentials not found in environment variables.")

# Create the supabase client (we will use this in our routes)
try:
    supabase: Client = create_client(url, key)
except Exception as e:
    print(f"Error initializing Supabase: {e}")
    supabase = None

def get_db():
    return supabase
