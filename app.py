from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shoppy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELS ====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# ==================== INIT DATABASE ====================
def init_db():
    with app.app_context():
        db.create_all()
        
        # Get passwords from environment variables (recommended for production)
        # Falls back to default values only for local development
        mhu_password = os.environ.get('MHU_PASSWORD', 'mhu123')
        cbr_password = os.environ.get('CBR_PASSWORD', 'cbr123')
        
        # Create default users if they don't exist
        if not User.query.filter_by(username='MHU').first():
            user1 = User(
                username='MHU',
                password_hash=generate_password_hash(mhu_password)
            )
            db.session.add(user1)
            print("Created user MHU")
        
        if not User.query.filter_by(username='CBR').first():
            user2 = User(
                username='CBR',
                password_hash=generate_password_hash(cbr_password)
            )
            db.session.add(user2)
            print("Created user CBR")
        
        db.session.commit()

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({
            'success': True,
            'username': user.username
        })
    
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/items', methods=['GET'])
def get_items():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    items = Item.query.order_by(Item.created_at.desc()).all()
    return jsonify([{
        'id': item.id,
        'text': item.text,
        'completed': item.completed
    } for item in items])

@app.route('/api/items', methods=['POST'])
def add_item():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    new_item = Item(text=text, completed=False)
    db.session.add(new_item)
    db.session.commit()
    
    return jsonify({
        'id': new_item.id,
        'text': new_item.text,
        'completed': new_item.completed
    }), 201

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/items/<int:item_id>/toggle', methods=['PATCH'])
def toggle_item(item_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    item = Item.query.get_or_404(item_id)
    item.completed = not item.completed
    db.session.commit()
    
    return jsonify({
        'id': item.id,
        'text': item.text,
        'completed': item.completed
    })

@app.route('/api/me')
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'logged_in': False})
    return jsonify({
        'logged_in': True,
        'username': session.get('username')
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)