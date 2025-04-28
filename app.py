import uuid
import datetime
import os
from functools import wraps
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
TOKEN_EXPIRATION = 3600

API_CLIENTS = {
    "client1": {"secret": "password1", "roles": ["admin"]},
    "client2": {"secret": "password2", "roles": ["read-only"]}
}

payments = {}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['client_id']
            user_roles = data['roles']

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user, user_roles, *args, **kwargs)

    return decorated


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "UP", "timestamp": datetime.datetime.now().isoformat()})


@app.route('/api/v1/auth/token', methods=['POST'])
def get_token():
    auth = request.json

    if not auth or not auth.get('client_id') or not auth.get('client_secret'):
        return jsonify({'error': 'Authentication required'}), 401

    client_id = auth.get('client_id')
    client_secret = auth.get('client_secret')

    if client_id not in API_CLIENTS or API_CLIENTS[client_id]['secret'] != client_secret:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generar token JWT
    payload = {
        'client_id': client_id,
        'roles': API_CLIENTS[client_id]['roles'],
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=TOKEN_EXPIRATION)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': TOKEN_EXPIRATION
    })


@app.route('/api/v1/payments', methods=['POST'])
@token_required
def approve_payment(current_user, user_roles):
    data = request.json

    if not data or not all(key in data for key in ['amount', 'cardNumber', 'cvv', 'expiryDate', 'currency']):
        return jsonify({"error": "Missing required payment information"}), 400

    if len(data['cardNumber']) < 13 or len(data['cardNumber']) > 19:
        return jsonify({"error": "Invalid card number"}), 400

    if len(data['cvv']) < 3 or len(data['cvv']) > 4:
        return jsonify({"error": "Invalid CVV"}), 400

    payment_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()

    status = "REJECTED" if data['cardNumber'].endswith('0000') else "APPROVED"

    payment = {
        "id": payment_id,
        "amount": data['amount'],
        "currency": data['currency'],
        "cardNumber": data['cardNumber'][-4:].rjust(len(data['cardNumber']), '*'),  # Enmascarar número de tarjeta
        "status": status,
        "timestamp": timestamp,
        "transactionReference": f"TX-{payment_id[:8]}",
        "lastUpdated": timestamp,
        "processedBy": current_user
    }

    payments[payment_id] = payment

    return jsonify(payment), 201 if status == "APPROVED" else 402


@app.route('/api/v1/payments/<payment_id>', methods=['GET'])
@token_required
def get_payment(current_user, user_roles, payment_id):
    payment = payments.get(payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    return jsonify(payment)


@app.route('/api/v1/payments/<payment_id>/reverse', methods=['POST'])
@token_required
def reverse_payment(current_user, user_roles, payment_id):
    if 'admin' not in user_roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    payment = payments.get(payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    if payment['status'] != "APPROVED":
        return jsonify({"error": "Only approved payments can be reversed"}), 400

    payment['status'] = "REVERSED"
    payment['lastUpdated'] = datetime.datetime.now().isoformat()
    payment['reversedBy'] = current_user

    return jsonify(payment)


@app.route('/api/v1/payments/<payment_id>/cancel', methods=['POST'])
@token_required
def cancel_payment(current_user, user_roles, payment_id):
    payment = payments.get(payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    if payment['status'] not in ["APPROVED", "PENDING"]:
        return jsonify({"error": "Only approved or pending payments can be cancelled"}), 400

    payment['status'] = "CANCELLED"
    payment['lastUpdated'] = datetime.datetime.now().isoformat()
    payment['cancelledBy'] = current_user

    return jsonify(payment)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
