#!/usr/bin/env python3
"""
Quick verification script for the enhanced AI Research Assistant
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_schema():
    """Verify database schema is correct"""
    print("🗄️  Checking database schema...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import psycopg2
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if full_text_content column exists
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'full_text_content'
        """)
        
        if cursor.fetchone():
            print("✅ full_text_content column exists in documents table")
        else:
            print("❌ full_text_content column missing from documents table")
            return False
        
        # Check if search_logs table exists
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'search_logs'
        """)
        
        if cursor.fetchone():
            print("✅ search_logs table exists")
        else:
            print("❌ search_logs table missing")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_imports():
    """Check if all required modules can be imported"""
    print("\n📦 Checking imports...")
    
    modules_to_check = [
        ('Flask', 'flask'),
        ('bcrypt', 'bcrypt'),
        ('psycopg2', 'psycopg2'),
        ('PyPDF2', 'PyPDF2'),
        ('docx', 'docx'),
        ('PIL', 'PIL'),
        ('pytesseract', 'pytesseract')
    ]
    
    all_good = True
    
    for display_name, module_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError as e:
            print(f"❌ {display_name}: {e}")
            all_good = False
    
    return all_good

def check_application_structure():
    """Check if all required files and directories exist"""
    print("\n📁 Checking application structure...")
    
    required_items = [
        ('main.py', 'file'),
        ('templates/', 'dir'),
        ('templates/search.html', 'file'),
        ('templates/view_document.html', 'file'),
        ('search/', 'dir'),
        ('search/algorithms.py', 'file'),
        ('utils/file_utils.py', 'file'),
        ('db/models.sql', 'file'),
        ('requirements.txt', 'file')
    ]
    
    all_good = True
    
    for item, item_type in required_items:
        path = os.path.join(os.path.dirname(__file__), item)
        
        if item_type == 'file' and os.path.isfile(path):
            print(f"✅ {item}")
        elif item_type == 'dir' and os.path.isdir(path):
            print(f"✅ {item}")
        else:
            print(f"❌ {item} ({'file' if item_type == 'file' else 'directory'} missing)")
            all_good = False
    
    return all_good

def check_search_functionality():
    """Quick test of search functionality"""
    print("\n🔍 Testing search functionality...")
    
    try:
        from search.algorithms import searcher, SearchResult
        print("✅ Search algorithms module imported successfully")
        
        # Test SearchResult class
        test_result = SearchResult(1, "test.txt", ["tag1"], "summary", "content", 0.8, "context", "filename")
        result_dict = test_result.to_dict()
        
        if 'document_id' in result_dict and 'match_score' in result_dict:
            print("✅ SearchResult class working correctly")
        else:
            print("❌ SearchResult class has issues")
            return False
        
        # Test text extraction
        from utils.file_utils import extract_text_from_file
        print("✅ Text extraction utilities imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Search functionality test failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🔍 AI Research Assistant - Enhanced Version Verification")
    print("=" * 60)
    
    all_checks = [
        check_imports(),
        check_application_structure(),
        check_database_schema(),
        check_search_functionality()
    ]
    
    print("\n" + "=" * 60)
    
    if all(all_checks):
        print("🎉 ALL CHECKS PASSED!")
        print("\n✅ Your AI Research Assistant is ready with search functionality!")
        print("\n🚀 Start the application:")
        print("   python main.py")
        print("\n🌐 Then open: http://localhost:5000")
        print("\n📚 Features available:")
        print("   • User authentication")
        print("   • File upload with text extraction")
        print("   • Intelligent search (BFS, DFS, A*)")
        print("   • Document viewing")
        print("   • Tag management")
        print("   • Search analytics")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("\nPlease review the errors above and fix them before running the application.")
        print("\n💡 Common fixes:")
        print("   • Install missing dependencies: pip install -r requirements.txt")
        print("   • Update database schema (run the schema update script)")
        print("   • Check file permissions")

if __name__ == "__main__":
    main()