import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load Supabase credentials from .env file
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
sb: Client = create_client(url, key)

# --- Task 1: Create (Insert) ---

def register_member(name, email):
    try:
        data = sb.table("members").insert({"name": name, "email": email}).execute()
        return data.data
    except Exception as e:
        print(f"Error registering member: {e}")
        return None

def add_book(title, author, category, stock):
    try:
        data = sb.table("books").insert({"title": title, "author": author, "category": category, "stock": stock}).execute()
        return data.data
    except Exception as e:
        print(f"Error adding book: {e}")
        return None

# --- Task 2: Read (Select) ---

def list_all_books():
    try:
        books = sb.table("books").select("*").execute()
        return books.data
    except Exception as e:
        print(f"Error fetching books: {e}")
        return None

def search_books(query, search_by):
    try:
        if search_by == 'title':
            books = sb.table("books").select("*").ilike('title', f'%{query}%').execute()
        elif search_by == 'author':
            books = sb.table("books").select("*").ilike('author', f'%{query}%').execute()
        elif search_by == 'category':
            books = sb.table("books").select("*").ilike('category', f'%{query}%').execute()
        return books.data
    except Exception as e:
        print(f"Error searching books: {e}")
        return None

def show_member_details(member_id):
    try:
        details = sb.table("members").select("*, borrow_records(title:books(title))").eq("member_id", member_id).execute()
        return details.data
    except Exception as e:
        print(f"Error fetching member details: {e}")
        return None

# --- Task 3: Update ---

def update_book_stock(book_id, new_stock):
    try:
        data = sb.table("books").update({"stock": new_stock}).eq("book_id", book_id).execute()
        return data.data
    except Exception as e:
        print(f"Error updating stock: {e}")
        return None

def update_member_info(member_id, new_email=None, new_name=None):
    try:
        update_data = {}
        if new_email:
            update_data['email'] = new_email
        if new_name:
            update_data['name'] = new_name
        data = sb.table("members").update(update_data).eq("member_id", member_id).execute()
        return data.data
    except Exception as e:
        print(f"Error updating member info: {e}")
        return None

# --- Task 4: Delete ---

def delete_member(member_id):
    try:
        # Check for any borrowed books first
        borrowed = sb.table("borrow_records").select("*").eq("member_id", member_id).is_("return_date", "null").execute()
        if borrowed.data:
            print("Cannot delete member: they have outstanding borrowed books.")
            return None
        
        data = sb.table("members").delete().eq("member_id", member_id).execute()
        return data.data
    except Exception as e:
        print(f"Error deleting member: {e}")
        return None

def delete_book(book_id):
    try:
        # Check if the book is currently borrowed
        borrowed = sb.table("borrow_records").select("*").eq("book_id", book_id).is_("return_date", "null").execute()
        if borrowed.data:
            print("Cannot delete book: it is currently borrowed.")
            return None
        
        data = sb.table("books").delete().eq("book_id", book_id).execute()
        return data.data
    except Exception as e:
        print(f"Error deleting book: {e}")
        return None

# --- Task 5 & 6: Borrow/Return (Transactions via RPC) ---

def borrow_book(member_id, book_id):
    try:
        response = sb.rpc("borrow_book_transaction", {"p_member_id": member_id, "p_book_id": book_id}).execute()
        return response.data
    except Exception as e:
        print(f"Error borrowing book: {e}")
        return None

def return_book(member_id, book_id):
    try:
        response = sb.rpc("return_book_transaction", {"p_member_id": member_id, "p_book_id": book_id}).execute()
        return response.data
    except Exception as e:
        print(f"Error returning book: {e}")
        return None

# --- Task 7: Reports (Advanced Selects) ---

def get_top_borrowed():
    try:
        query = sb.table("borrow_records").select("book_id", count="count()").group("book_id").order("count", desc=True).limit(5)
        books_with_details = query.select("*, book:books(title)").execute()
        return books_with_details.data
    except Exception as e:
        print(f"Error getting top borrowed books: {e}")
        return None

def get_overdue_books():
    try:
        # Join borrow_records with books and members to get details
        # Check for borrow_date > 14 days ago and return_date is null
        overdue_books = sb.table("borrow_records").select("*, member:members(name), book:books(title)").gte('borrow_date', 'now()-14d').is_('return_date', 'null').execute()
        return overdue_books.data
    except Exception as e:
        print(f"Error getting overdue books: {e}")
        return None
    
def get_borrow_count_per_member():
    try:
        query = sb.table("borrow_records").select("member_id", count="count()").group("member_id").order("count", desc=True)
        members_with_details = query.select("*, member:members(name)").execute()
        return members_with_details.data
    except Exception as e:
        print(f"Error getting borrow count: {e}")
        return None

# --- Command-Line Interface ---

if __name__ == "__main__":
    while True:
        print("\n--- Library Management System Menu ---")
        print("1. Register a new member")
        print("2. Add a new book")
        print("3. List all books")
        print("4. Search for a book")
        print("5. Update book stock")
        print("6. Update member info")
        print("7. Delete a member")
        print("8. Delete a book")
        print("9. Borrow a book")
        print("10. Return a book")
        print("11. Generate reports")
        print("12. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            name = input("Enter member name: ")
            email = input("Enter member email: ")
            register_member(name, email)
            print("Member registered.")

        elif choice == '2':
            title = input("Enter book title: ")
            author = input("Enter author: ")
            category = input("Enter category: ")
            stock = int(input("Enter stock count: "))
            add_book(title, author, category, stock)
            print("Book added.")
        
        elif choice == '3':
            books = list_all_books()
            for book in books:
                print(f"Title: {book['title']}, Author: {book['author']}, Stock: {book['stock']}")

        elif choice == '4':
            search_by = input("Search by (title/author/category): ")
            query = input("Enter your search query: ")
            books = search_books(query, search_by)
            for book in books:
                print(f"Title: {book['title']}, Author: {book['author']}, Stock: {book['stock']}")

        elif choice == '5':
            book_id = int(input("Enter book ID to update stock: "))
            new_stock = int(input("Enter new stock count: "))
            update_book_stock(book_id, new_stock)
            print("Book stock updated.")
        
        elif choice == '6':
            member_id = int(input("Enter member ID to update: "))
            new_name = input("Enter new name (leave blank to skip): ")
            new_email = input("Enter new email (leave blank to skip): ")
            update_member_info(member_id, new_email, new_name)
            print("Member info updated.")

        elif choice == '7':
            member_id = int(input("Enter member ID to delete: "))
            delete_member(member_id)
            print("Member deleted if they had no outstanding books.")

        elif choice == '8':
            book_id = int(input("Enter book ID to delete: "))
            delete_book(book_id)
            print("Book deleted if it is not currently borrowed.")

        elif choice == '9':
            member_id = int(input("Enter member ID: "))
            book_id = int(input("Enter book ID to borrow: "))
            result = borrow_book(member_id, book_id)
            print(result)

        elif choice == '10':
            member_id = int(input("Enter member ID: "))
            book_id = int(input("Enter book ID to return: "))
            result = return_book(member_id, book_id)
            print(result)

        elif choice == '11':
            print("--- Generating Reports ---")
            print("Top 5 Most Borrowed Books:")
            top_books = get_top_borrowed()
            for book in top_books:
                print(f"Title: {book['book']['title']}, Borrow Count: {book['count']}")
            
            print("\nMembers with Overdue Books:")
            overdue_books = get_overdue_books()
            for record in overdue_books:
                print(f"Member: {record['member']['name']}, Book: {record['book']['title']}, Borrowed On: {record['borrow_date']}")

            print("\nTotal Books Borrowed per Member:")
            borrow_counts = get_borrow_count_per_member()
            for record in borrow_counts:
                print(f"Member: {record['member']['name']}, Total Books: {record['count']}")

        elif choice == '12':
            print("Exiting.")
            break

        else:
            print("Invalid choice. Please enter a number from 1 to 12.")