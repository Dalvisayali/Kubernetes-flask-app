from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI','postgresql://postgres:postgres@localhost:5432/mydatabase')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Users {self.name}>'

# Initialize the database
@app.before_first_request
def create_tables():
    db.create_all()

# Health check API
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# Get user details API
@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = Users.query.get(user_id)
    if user:
        return jsonify({'id': user.id, 'name': user.name, 'email': user.email}), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# Create user API
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or not 'name' in data or not 'email' in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    new_user = Users(name=data['name'], email=data['email'])
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'User with this email already exists'}), 409
    
    return jsonify({'message': 'User created', 'user': {'id': new_user.id, 'name': new_user.name, 'email': new_user.email}}), 201

# Update user details API
@app.route('/user/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    data = request.get_json()
    user = Users.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if Users.query.filter_by(email=data['email']).first() and user.email != data['email']:
            return jsonify({'error': 'Email already in use'}), 409
        user.email = data['email']

    db.session.commit()
    return jsonify({'message': 'User updated', 'user': {'id': user.id, 'name': user.name, 'email': user.email}}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
