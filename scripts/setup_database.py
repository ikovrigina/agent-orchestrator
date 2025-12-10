#!/usr/bin/env python3
"""
Database Setup Script
Creates tables in Supabase and syncs projects from config
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def setup_database():
    """Set up the database"""
    from supabase_manager import SupabaseManager
    
    print("🗄️ Setting up database...")
    
    try:
        manager = SupabaseManager()
        
        # Sync projects from config
        print("📦 Syncing projects from config...")
        manager.sync_projects_from_config()
        
        # Show current projects
        projects = manager.get_all_projects()
        print(f"\n✅ {len(projects)} projects in database:")
        for p in projects:
            print(f"   - {p['name']} ({p['status']})")
        
        print("\n✨ Database setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Database setup failed")
        sys.exit(1)


def read_schema():
    """Read and display the SQL schema"""
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        "config", 
        "supabase_schema.sql"
    )
    
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            print("\n📋 SQL Schema:\n")
            print(f.read())
    else:
        print("❌ Schema file not found")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--schema":
        read_schema()
    else:
        setup_database()

