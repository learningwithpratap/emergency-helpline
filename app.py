# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS # For handling cross-origin requests
from pymongo import MongoClient
from bson.objectid import ObjectId # To work with MongoDB's default _id
import os
import datetime

from flask_socketio import SocketIO, emit
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import datetime
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["emergency_lifeline_db"]

# Broadcast new alert
@app.route('/api/public-alerts', methods=['POST'])
def create_alert():
    data = request.get_json()
    data["timestamp"] = datetime.datetime.utcnow()

    db.alerts.insert_one(data)
    alert_id = str(data.get("_id", ""))

    # Emit alert to all connected clients
    socketio.emit('new_alert', {
        "title": data["title"],
        "message": data["message"],
        "severity": data["severity"],
        "timestamp": data["timestamp"].isoformat()
    })

    return jsonify({"message": "Alert sent", "alert_id": alert_id}), 200

@app.route('/api/public-alerts', methods=['GET'])
def get_alerts():
    alerts = list(db.alerts.find().sort("timestamp", -1))
    for alert in alerts:
        alert['_id'] = str(alert['_id'])
        alert['timestamp'] = alert['timestamp'].isoformat()
    return jsonify(alerts), 200

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=5000)

# from dotenv import load_dotenv # Uncomment if using .env file for MONGO_URI

# load_dotenv() # Load environment variables from .env file

app = Flask(__name__)
CORS(app) # Enable CORS for all routes, allowing your frontend to access it from a different origin

# --- MongoDB Configuration ---
# IMPORTANT: Replace with your actual MongoDB connection string.
# For local MongoDB: "mongodb://localhost:27017/"
# For MongoDB Atlas: "mongodb+srv://<username>:<password>@<cluster-url>/<database-name>?retryWrites=true&w=majority"
# It's highly recommended to use environment variables for sensitive info like MONGO_URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/") # Fallback to local if env var not set
DB_NAME = "emergency_lifeline_db" # Your database name

client = None # Initialize client as None
db = None     # Initialize db as None

def connect_to_mongodb():
    """Establishes connection to MongoDB."""
    global client, db
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        print(f"Successfully connected to MongoDB: {MONGO_URI.split('@')[-1]}") # Print connection status (without password)
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        # Optionally, you might want to exit or handle this more gracefully in a production app
        exit(1)

# Ensure connection is established when the app starts
with app.app_context():
    connect_to_mongodb()


# Helper function to get current user ID (for demonstration purposes)
# In a real app, this would come from an authentication system (e.g., JWT, session)
def get_current_user_id():
    # Placeholder: In a real application, this would derive from a user session or token.
    # For now, we'll use a fixed ID or assume it's passed.
    # You might get it from request.headers, request.args, or a JWT payload.
    return request.headers.get('X-User-ID', 'demo_user_123') # Default for testing


# --- API Routes ---

@app.route('/')
def home():
    return "Emergency Lifeline Backend is running!"

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """
    Retrieves user profile information.
    In a real application, this would fetch from a 'users' collection.
    """
    user_id = get_current_user_id()
    users_collection = db["users"] # Assume a 'users' collection

    try:
        # For demonstration, let's return a dummy profile or fetch a real one if it exists
        user_profile = users_collection.find_one({"_id": ObjectId(user_id)}) # If _id is ObjectId
        if not user_profile:
            # Create a dummy profile if not found
            dummy_profile = {
                "_id": ObjectId(user_id),
                "name": "Demo User",
                "blood_type": "O+",
                "allergies": ["None"],
                "medical_conditions": ["None"],
                "emergency_contact_ids": [] # Store IDs of contacts in a separate collection
            }
            users_collection.insert_one(dummy_profile)
            user_profile = dummy_profile
        
        # Convert ObjectId to string for JSON serialization
        user_profile['_id'] = str(user_profile['_id'])
        return jsonify(user_profile), 200
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return jsonify({"error": "Failed to fetch profile", "details": str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def update_profile():
    """
    Updates user profile information.
    """
    user_id = get_current_user_id()
    users_collection = db["users"]
    data = request.json

    try:
        update_result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": data},
            upsert=True # Create if not exists
        )
        if update_result.matched_count > 0 or update_result.upserted_id:
            return jsonify({"message": "Profile updated successfully"}), 200
        else:
            return jsonify({"message": "No changes made to profile"}), 200 # Or 400 if no data
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({"error": "Failed to update profile", "details": str(e)}), 500

@app.route('/api/emergency_contacts', methods=['GET'])
def get_emergency_contacts():
    """
    Retrieves emergency contacts for the current user.
    """
    user_id = get_current_user_id()
    contacts_collection = db[f"users/{user_id}/emergency_contacts"] # User-specific collection

    try:
        contacts = []
        for contact in contacts_collection.find():
            contact['_id'] = str(contact['_id']) # Convert ObjectId to string
            contacts.append(contact)
        return jsonify({"contacts": contacts}), 200
    except Exception as e:
        print(f"Error retrieving contacts: {e}")
        return jsonify({"error": "Failed to retrieve contacts", "details": str(e)}), 500

@app.route('/api/emergency_contacts', methods=['POST'])
def add_emergency_contact():
    """
    Adds a new emergency contact for the current user.
    """
    user_id = get_current_user_id()
    contacts_collection = db[f"users/{user_id}/emergency_contacts"]
    data = request.json

    name = data.get('name')
    relationship = data.get('relationship')
    phone = data.get('phone')

    if not all([name, relationship, phone]):
        return jsonify({"error": "Missing required fields (name, relationship, phone)"}), 400

    try:
        new_contact = {
            "name": name,
            "relationship": relationship,
            "phone": phone,
            "added_at": datetime.datetime.utcnow()
        }
        result = contacts_collection.insert_one(new_contact)
        new_contact['_id'] = str(result.inserted_id) # Convert ObjectId to string
        return jsonify({"message": "Contact added successfully", "contact": new_contact}), 201
    except Exception as e:
        print(f"Error adding contact: {e}")
        return jsonify({"error": "Failed to add contact", "details": str(e)}), 500

@app.route('/api/emergency_contacts/<contact_id>', methods=['DELETE'])
def delete_emergency_contact(contact_id):
    """
    Deletes an emergency contact.
    """
    user_id = get_current_user_id()
    contacts_collection = db[f"users/{user_id}/emergency_contacts"]

    try:
        result = contacts_collection.delete_one({"_id": ObjectId(contact_id)})
        if result.deleted_count > 0:
            return jsonify({"message": "Contact deleted successfully"}), 200
        else:
            return jsonify({"error": "Contact not found"}), 404
    except Exception as e:
        print(f"Error deleting contact: {e}")
        return jsonify({"error": "Failed to delete contact", "details": str(e)}), 500

@app.route('/api/alerts/send', methods=['POST'])
def send_emergency_alert():
    """
    Sends an emergency alert to designated contacts.
    In a real app, this would trigger SMS/email notifications.
    """
    user_id = get_current_user_id()
    # For simplicity, let's assume all contacts are emergency contacts for alerting
    contacts_collection = db[f"users/{user_id}/emergency_contacts"]
    alerts_collection = db[f"users/{user_id}/emergency_alerts"]

    data = request.json
    message = data.get('message', 'Emergency! I need help.')
    location = data.get('location', 'Location not provided.') # Example: "Latitude: X, Longitude: Y"

    try:
        recipients_list = []
        for contact in contacts_collection.find():
            recipients_list.append(contact)
            # In a real app, you would send SMS/email here
            print(f"Simulating alert to {contact['name']} ({contact['phone']}): {message} at {location}")

        if not recipients_list:
            return jsonify({"message": "No emergency contacts found to send alert."}), 200

        # Log the alert
        alerts_collection.insert_one({
            "timestamp": datetime.datetime.utcnow(),
            "message": message,
            "location": location,
            "recipients": [str(r['_id']) for r in recipients_list] # Store contact IDs
        })

        return jsonify({
            "message": "Alert initiated successfully",
            "recipients_count": len(recipients_list),
            "recipients": [r['name'] for r in recipients_list] # Return names for frontend display
        }), 200
    except Exception as e:
        print(f"Error sending alert: {e}")
        return jsonify({"error": "Failed to send alert", "details": str(e)}), 500

@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """
    Retrieves the emergency alert history for the current user.
    """
    user_id = get_current_user_id()
    alerts_collection = db[f"users/{user_id}/emergency_alertsَص"]