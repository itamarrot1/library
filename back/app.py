from flask import Flask,request,jsonify,redirect, send_from_directory,url_for,make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime,timedelta


app = Flask(__name__)
# configure the SQLite database, relative to the app instance folderf
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'jwt_secret_key_here'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(),'uploads')
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=True)
    loans=db.Column(db.Integer, nullable=False, default=0)
    loans_con= db.relationship('Loans', backref='user')


    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    photo_path = db.Column(db.String(255))
    loan_by=db.Column(db.Integer, db.ForeignKey('user.id'))
    type = db.Column(db.Integer, nullable=False, default=1) 

    def __repr__(self):
        return f'<Book {self.title}>'

class Loans(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    book_id=db.Column(db.Integer,db.ForeignKey('book.id'))
    loan_date = db.Column(db.DateTime, default=datetime.now(), nullable=False) 
    require_return_date = db.Column(db.DateTime)
                            
                            
class ArchivedLoans(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    loan_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    on_time= db.Column(db.String)

@app.route('/add_books', methods=['POST'])
@jwt_required()
def add_book():
    print("check 1")
    
    file= request.files['book_photo']
    title= request.form.get('title')
    author=request.form.get('author')
    book_type = int(request.form.get('type')) 
    if 'book_photo' not in request.files:
        return jsonify ({'error':'no book photo has been uploded'})

    print(file.filename)
    book_photo=secure_filename(file.filename)
    print(os.path.join(app.config['UPLOAD_FOLDER'],book_photo))
    file.save(os.path.join(app.config['UPLOAD_FOLDER'],book_photo))

    new_book=Book(title=title,author=author,photo_path=book_photo,type=book_type)
    db.session.add(new_book)
    db.session.commit()
    return (jsonify ({'messege': 'book added'}), 200) 
 
@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/user-role', methods=['GET'])
@jwt_required()
def get_user_role():
    print('check 1')
    try:
        print('check 2')
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Return user role information
        return jsonify({'username': user.username, 'admin': user.admin}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/display_loans', methods=['GET'])
@jwt_required()
def display_loans():
    try:
        # Perform a join to get loans with associated user names and book titles
        loans_with_users_books = db.session.query(Loans, User.username, Book.title).\
            join(User, Loans.user_id == User.id).\
            join(Book, Loans.book_id == Book.id).all()

        loans_data = []
        for loan, username, book_title in loans_with_users_books:
            loan_data = {
                'id': loan.id,
                'user_id': loan.user_id,
                'book_id': loan.book_id,
                'loan_date': loan.loan_date.strftime('%Y-%m-%d %H:%M:%S'),  # Format loan_date as string
                'username': username,
                'book_title': book_title  # Add book_title to loan data
            }
            loans_data.append(loan_data)

        return jsonify(loans_data)
    
    except Exception as e:
        print(f"Error fetching loans: {e}")
        return jsonify({'error': 'Failed to fetch loans'}), 500

@app.route('/display_books', methods=['GET'])
@jwt_required()
def display_books():
    try:
        current_user_id = get_jwt_identity()

        # Query all books
        books = Book.query.all()

        # Query current user's username based on user's ID
        current_user = User.query.filter_by(id=current_user_id).first()

        if not current_user:
            return jsonify({'error': 'User not found'}), 404

        # Create a list of dictionaries for books
        book_list = []
        for book in books:
            book_info = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'is_available': book.is_available,
                'photo_path': book.photo_path,
                'loan_by': book.loan_by,
                'type': book.type
            }
            book_list.append(book_info)

        # Append current user's username to the response
        response_data = {
            'books': book_list,
            'username': current_user.username,
            'admin' : current_user.admin
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve books: {str(e)}'}), 500


@app.route('/Register', methods=['POST'])
def user_create():
    data = request.get_json()
    username=data.get("username")
    password=data.get("password")
    email=data.get("email")
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400 
       
    password_hash = generate_password_hash(password)
    user=User(username=username, password_hash=password_hash ,email=email)
    db.session.add(user)
    db.session.commit()
    print (user)
    return  jsonify({'messege':'f"{user}    added "'})


@app.route('/sign-in',methods=['POST'])
def sign_in():

    data = request.get_json()
    username=data.get("username")
    password=data.get("password")
    user = User.query.filter_by(username=username).first() 
    if not user or not check_password_hash(user.password_hash, password): #123 after encript = to scrypt:32768:8:1$rmqHNat7nzuoXlrr$91d9cc8e2c03f57be624ce3d273b02f77772a0a3dfbdf025927550f86724dd3b2a0e047ecc12480c62aeabb66d14d6cc81519c335cca5d73cf8563e4b1516af0
        return jsonify({'message': 'username or password not exsist'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200
    
@app.route('/hello',methods=['GET'])
@jwt_required()
def hello():
    current_user = get_jwt_identity()
    return jsonify({'message': f'Hello, {current_user}! This is a private endpoint.'}), 200


@app.route('/display_connected_user_details', methods=['GET'])
@jwt_required()
def display_connected_user_detailes():
    current_user_id = get_jwt_identity()  # Get user's ID
    user = User.query.filter_by(id=current_user_id).first()
    user_detiles= {
         'id': user.id,
        'username' : user.username,
        'email' : user.email,
        'loans':user.loans
    }
    print (user_detiles)
    return jsonify(user_detiles)

@app.route('/display_users', methods=['GET'])
@jwt_required()
def display_users():
    all_users = User.query.all()
    
    # Construct list of dictionaries containing username and email
    users_list = []
    for user in all_users:
        users_list.append({
            'id':user.id,
            'username': user.username,
            'email': user.email
        })
        print(users_list)
    return jsonify(users_list)


@app.route('/delete_user/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    del_user = User.query.get(id)

    if not del_user:
        return jsonify({'message': f'User with id {id} not found'}), 404

    # Check if there are active loans for the user
    active_loans = Loans.query.filter_by(user_id=del_user.id).all()
    if active_loans:
        return jsonify({'message': 'Cannot delete user. Active loans exist.'}), 400

    # If no active loans exist, proceed with deleting the user
    db.session.delete(del_user)
    db.session.commit()

    return jsonify({'message': f'User {id} has been deleted successfully'}), 200

@app.route('/update_user', methods=['PUT', 'PATCH'])
@jwt_required()
def update_user():
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=current_user_id).first()

    if not user:
        return jsonify({'message': f'User with ID {current_user_id} not found'}), 404

    # Get books loaned by the user
    books_loaned_by_user = Book.query.filter_by(loan_by=user.username).all()

    # Update user data based on request JSON data
    data = request.json
    if 'username' in data and data['username'] != user.username:
        new_username = data['username']
        old_username = user.username
        user.username = new_username
        
        # Update loan_by field in all books loaned by the user
        for book in books_loaned_by_user:
            book.loan_by = new_username
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {old_username} updated to {new_username}. Books updated successfully.'
        }), 200
    
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    
    return jsonify({'message': f'User {user.username} has been updated successfully'}), 200

@app.route('/book/<int:id>', methods=['GET'])
@jwt_required()
def get_book_details(id):
    try:
        current_user = get_jwt_identity()
        book = Book.query.get(id)
        
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        book_details = {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'photo_path': book.photo_path,
            'loan_by': book.loan_by,
            'is_available': book.is_available
        }
        
        response_data = {
            'book_details': book_details,
            'username': current_user
        }
        print(response_data)
        return jsonify(response_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/my_loans', methods=['GET'])
@jwt_required()
def display_user_loans():
    try:
        current_user_id = get_jwt_identity()
        
        # Query loans with user, book details based on user's ID
        loans_with_users_books = db.session.query(Loans, User.username, Book).\
            join(User, Loans.user_id == User.id).\
            join(Book, Loans.book_id == Book.id).\
            filter(Loans.user_id == current_user_id).all()

        # Prepare the response JSON
        loans_data = []
        for loan, username, book in loans_with_users_books:
            formatted_return_date = loan.require_return_date.date().isoformat()
            book_info = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'is_available': book.is_available,
                'photo_path': book.photo_path,
                'loan_by': book.loan_by,
                'type': book.type,
                'require_return_date': formatted_return_date
            }
            loan_info = {
                'loan_id': loan.id,
                'username': username,  # Use the fetched username from the query
                'book': book_info,
                # Add more fields as needed
            }
            loans_data.append(loan_info)

        return jsonify({'loans': loans_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/search', methods=['POST'])
@jwt_required()
def search_books():
    try:
        data = request.get_json()
        search_query = data.get('search')

        if not search_query:
            return jsonify({'error': 'Query parameter "search" is required'}), 400

        # Query books based on search_query (case-insensitive search)
        books = Book.query.filter(Book.title.ilike(f'%{search_query}%')).all()

        if books:
            # Create a list of dictionaries for books
            book_list = []
            print("Books found:", books)  # Debug statement

            for book in books:
                print(f"Processing book: {book.title}")  # Debug statement

                book_details = {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'is_available': book.is_available,
                    'photo_path': book.photo_path,
                    'loan_by': book.loan_by if book.loan_by else 'None',
                    'type': book.type
                }
                book_list.append(book_details)
                print(book_list)
            # Append current user's username to the response
            current_user = get_jwt_identity()
            response_data = {
                'books': book_list,
                'username': current_user
            }

            return jsonify(response_data), 200
        else:
            return jsonify({'error': 'No books found for the given query'}), 404

    except Exception as e:
        return jsonify({'error': f'Failed to search books: {str(e)}'}), 500
    
@app.route('/loanbook/<int:id>', methods=['POST'])
@jwt_required()
def loan_book(id):
    try:
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()

        # Retrieve the user from the database
        loaned_user = User.query.filter_by(id=current_user_id).first()
        if not loaned_user:
            return jsonify({"error": "User not found"}), 404

        # Retrieve the book from the database
        loaned_book = Book.query.get(id)
        if not loaned_book:
            return jsonify({"error": "Book not found"}), 404

        # Check if the book is available for loan
        if not loaned_book.is_available:
            return jsonify({"error": "Book is already loaned"}), 400

        # Determine loan duration based on book type
        if loaned_book.type == 1:
            loan_duration = timedelta(days=10)
        elif loaned_book.type == 2:
            loan_duration = timedelta(days=7)
        elif loaned_book.type == 3:
            loan_duration = timedelta(days=2)
        else:
            loan_duration = timedelta(days=7)  # Default to 7 days if type is not recognized

        # Calculate return date
        return_date = datetime.now() + loan_duration

        # Proceed with loaning the book
        new_loan_entry = Loans(user_id=loaned_user.id, book_id=loaned_book.id,  require_return_date=return_date)
        db.session.add(new_loan_entry)

        # Update book status and loan information
        loaned_book.is_available = False
        print(loaned_book.is_available)
        loaned_book.loan_by = loaned_user.username  # Store user ID who loans the book (using user ID)
        loaned_user.loans += 1  # Increment loans count
        db.session.commit()

        return jsonify({"message": "Book loaned successfully", "return_date": return_date.strftime('%Y-%m-%d')}), 200

    except Exception as e:
        print('Error:', str(e))
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/returnbook/<int:id>', methods=['DELETE'])
@jwt_required()
def return_book(id):
    if request.method == 'DELETE':
        print(id)
        print("כגד")
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        print('Current User ID (username):', current_user_id)

        # Retrieve the user from the database based on username
        loaned_user = User.query.filter_by(id=current_user_id).first()
        avalibale_again= Book.query.get(id)
        # Check if the user exists
        if not loaned_user:
            print('User not found')
            return jsonify({"error": "User not found"}), 404
        print(loaned_user.id)
        # Check if the user has loaned the book
        existing_loan = Loans.query.filter_by(user_id=loaned_user.id, book_id=id).first()
        print(existing_loan)
        if existing_loan:
            if existing_loan.require_return_date > datetime.now():
                return_status = 'on time'
            else:
                return_status = 'late'
            # Archive the loan
            archived_loan = ArchivedLoans(
                user_id=existing_loan.user_id,
                book_id=existing_loan.book_id,
                loan_date=existing_loan.loan_date,
                return_date=datetime.now(),
                on_time= return_status  # Example: Use current time as return date
            )
            db.session.add(archived_loan)
            print(existing_loan)
            avalibale_again.is_available = True
            avalibale_again.loan_by= None
            db.session.delete(existing_loan)
            db.session.commit()

            print('Book returned and archived successfully')
            return jsonify({"message": "Book returned and archived"}), 200
        else:
            print('User has not loaned this book')
            return jsonify({"error": "User has not loaned this book"}), 400

@app.route('/display_archived_loans', methods=['GET'])
@jwt_required()
def display_archived_loans():
    print("fsdf")
    try:
        print("fds")
        archived_loans = ArchivedLoans.query.all()
        
        # Serialize data
        serialized_loans = []
        for loan in archived_loans:
            serialized_loan = {
                'id': loan.id,
                'user_id': loan.user_id,
                'book_id': loan.book_id,
                'loan_date': loan.loan_date.strftime('%Y-%m-%d'),  # Format date as string
                'return_date': loan.return_date.strftime('%Y-%m-%d') if loan.return_date else None,
                'on_time': loan.on_time
            }
            serialized_loans.append(serialized_loan)
        print(serialized_loans)
        return jsonify(serialized_loans), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/delete_book/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_book(id):
    current_user_id = get_jwt_identity()
    current_user = User.query.filter_by(id=current_user_id).first()

    # Check if current user is an admin
    if not current_user or not current_user.admin:
        return jsonify({'message': 'Unauthorized. Admin permission required.'}), 401

    # Retrieve the book to delete
    book_to_delete = Book.query.get(id)

    # Check if the book exists
    if not book_to_delete:
        return jsonify({'message': f'Book with id {id} not found'}), 404

    # Check if there are active loans for the book
    active_loans = Loans.query.filter_by(book_id=id).all()
    if active_loans:
        return jsonify({'message': 'Cannot delete book. Active loans exist.'}), 400

    # Delete the book from the database
    db.session.delete(book_to_delete)
    db.session.commit()

    return jsonify({'message': f'Book with id {id} has been deleted successfully'}), 200



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)