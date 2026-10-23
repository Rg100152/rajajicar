import math
import os
import random
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
app.secret_key = 'rajajicar_midnight_neon_secret_key'

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rajajicar.db')


# ==========================================
# 1. DATABASE INITIALIZATION & SEEDING
# ==========================================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # Cars Fleet Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            transmission TEXT NOT NULL,
            fuel TEXT NOT NULL,
            seats INTEGER NOT NULL,
            hp TEXT NOT NULL,
            price_per_day INTEGER NOT NULL,
            reg_number TEXT NOT NULL,
            driver_name TEXT NOT NULL,
            status TEXT DEFAULT 'Available',
            total_km_run INTEGER DEFAULT 1200,
            last_service_km INTEGER DEFAULT 0,
            image_url TEXT NOT NULL,
            lat REAL DEFAULT 28.6139,
            lng REAL DEFAULT 77.2090
        )
    ''')

    # Bookings Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_ref TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            car_id INTEGER NOT NULL,
            car_name TEXT NOT NULL,
            booking_type TEXT NOT NULL,
            pickup_location TEXT NOT NULL,
            dropoff_location TEXT NOT NULL,
            pickup_datetime TEXT NOT NULL,
            return_datetime TEXT NOT NULL,
            distance_km INTEGER NOT NULL,
            days INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            base_fare INTEGER NOT NULL,
            tax_amount INTEGER NOT NULL,
            total_fare INTEGER NOT NULL,
            otp TEXT NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Drivers Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            car_model TEXT NOT NULL,
            reg_number TEXT NOT NULL,
            rating REAL DEFAULT 4.9,
            license_no TEXT NOT NULL,
            aadhar_verified INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Approved',
            earnings_today INTEGER DEFAULT 2450,
            rides_completed INTEGER DEFAULT 12,
            online_hours REAL DEFAULT 6.5
        )
    ''')

    # Settings Table (Dynamic Surge Pricing)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            surge_multiplier REAL DEFAULT 1.0,
            active_period TEXT DEFAULT 'Normal Hours (1.0x)',
            loyalty_bonus_rate INTEGER DEFAULT 10
        )
    ''')

    # Users / Loyalty Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            loyalty_points INTEGER DEFAULT 250,
            referral_code TEXT DEFAULT 'RAJAJI500',
            referred_by TEXT
        )
    ''')

    # Seed settings
    c.execute('SELECT COUNT(*) FROM settings')
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO settings (surge_multiplier, active_period, loyalty_bonus_rate) VALUES (1.0, 'Normal Hours (1.0x)', 10)"
        )

    # Seed default user
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO users (name, phone, loyalty_points, referral_code) VALUES ('Rajesh Sharma', '+91 98765 43210', 350, 'RAJAJIVIP')"
        )

    # Seed Cars Fleet
    c.execute('SELECT COUNT(*) FROM cars')
    if c.fetchone()[0] == 0:
        fleet_data = [
            (
                'BMW M3 Competition',
                'BMW',
                'Luxury',
                'Auto',
                'Petrol',
                4,
                '503 HP',
                8500,
                'DL 01 BM 0003',
                'Vikram Rathore',
                'Available',
                4850,
                0,
                'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80',
                28.6139,
                77.2090,
            ),
            (
                'Mercedes-Benz E-Class',
                'Mercedes-Benz',
                'Luxury',
                'Auto',
                'Diesel',
                5,
                '282 HP',
                9000,
                'MH 02 MB 7777',
                'Amit Singh',
                'Available',
                5300,
                0,
                'https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=800&q=80',
                28.6280,
                77.2190,
            ),
            (
                'Range Rover Velar',
                'Range Rover',
                'Luxury',
                'Auto',
                'Petrol',
                5,
                '395 HP',
                11500,
                'DL 03 RR 9999',
                'Karanveer Gill',
                'On Trip',
                3100,
                1000,
                'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=800&q=80',
                28.5921,
                77.1855,
            ),
            (
                'Porsche 911 Carrera',
                'Porsche',
                'Luxury',
                'Auto',
                'Petrol',
                2,
                '473 HP',
                15000,
                'HR 26 PR 0911',
                'Rohan Kapoor',
                'Available',
                2400,
                0,
                'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=800&q=80',
                28.6350,
                77.2245,
            ),
            (
                'Toyota Fortuner Legender',
                'Toyota',
                'SUV',
                'Auto',
                'Diesel',
                7,
                '201 HP',
                5500,
                'DL 01 AB 1234',
                'Rajesh Kumar',
                'Available',
                6200,
                1000,
                'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80',
                28.6100,
                77.2300,
            ),
            (
                'Mahindra Thar 4x4',
                'Mahindra',
                'SUV',
                'Manual',
                'Diesel',
                4,
                '150 HP',
                4000,
                'UP 16 TH 4444',
                'Deepak Chauhan',
                'Available',
                4200,
                0,
                'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=800&q=80',
                28.6050,
                77.2150,
            ),
            (
                'Tata Nexon EV Empowered',
                'Tata',
                'SUV',
                'Auto',
                'EV',
                5,
                '143 HP',
                3200,
                'KA 03 EV 9012',
                'Sandeep Patel',
                'Available',
                1900,
                0,
                'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=800&q=80',
                28.6200,
                77.2010,
            ),
            (
                'Honda City ZX Sedan',
                'Honda',
                'Sedan',
                'Manual',
                'Petrol',
                5,
                '119 HP',
                2800,
                'DL 04 HC 5521',
                'Manoj Tiwari',
                'Servicing',
                10400,
                5000,
                'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80',
                28.6410,
                77.2120,
            ),
            (
                'Audi A6 Matrix',
                'Audi',
                'Luxury',
                'Auto',
                'Petrol',
                5,
                '241 HP',
                8200,
                'DL 09 AU 0006',
                'Arjun Nair',
                'Available',
                3900,
                0,
                'https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=800&q=80',
                28.6180,
                77.1950,
            ),
        ]
        c.executemany(
            '''
            INSERT INTO cars (name, brand, category, transmission, fuel, seats, hp, price_per_day, reg_number, driver_name, status, total_km_run, last_service_km, image_url, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            fleet_data,
        )

    # Seed Drivers
    c.execute('SELECT COUNT(*) FROM drivers')
    if c.fetchone()[0] == 0:
        drivers_data = [
            (
                'Rajesh Kumar',
                '+91 98111 22334',
                'Toyota Fortuner Legender',
                'DL 01 AB 1234',
                4.9,
                'DL-01201900451',
                1,
                'Approved',
                2450,
                12,
                6.5,
            ),
            (
                'Suresh Yadav',
                '+91 98765 43210',
                'Hyundai Creta SX',
                'UP 32 CR 8812',
                4.7,
                'UP-32202100892',
                1,
                'Pending',
                0,
                0,
                0.0,
            ),
            (
                'Amit Singh',
                '+91 99223 34455',
                'Mercedes-Benz E-Class',
                'MH 02 MB 7777',
                5.0,
                'MH-02201800119',
                1,
                'Approved',
                4200,
                8,
                7.2,
            ),
            (
                'Pradeep Verma',
                '+91 97112 23388',
                'Kia Seltos GTX',
                'DL 08 KS 3310',
                4.6,
                'DL-08202200340',
                1,
                'Pending',
                0,
                0,
                0.0,
            ),
        ]
        c.executemany(
            '''
            INSERT INTO drivers (name, phone, car_model, reg_number, rating, license_no, aadhar_verified, status, earnings_today, rides_completed, online_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            drivers_data,
        )

    # Seed sample Bookings
    c.execute('SELECT COUNT(*) FROM bookings')
    if c.fetchone()[0] == 0:
        bookings_data = [
            (
                'RC-88241',
                'Rajesh Sharma',
                '+91 98765 43210',
                5,
                'Toyota Fortuner Legender',
                'Instant',
                'Connaught Place, New Delhi',
                'IGI Airport Terminal 3, Delhi',
                '2026-10-23 14:00',
                '2026-10-24 14:00',
                150,
                1,
                'UPI',
                7500,
                1350,
                8850,
                '4829',
                'Active Ride',
            ),
            (
                'RC-77410',
                'Rajesh Sharma',
                '+91 98765 43210',
                1,
                'BMW M3 Competition',
                'Scheduled',
                'Cyber Hub, Gurugram',
                'Jaipur Marriott Hotel',
                '2026-10-15 09:00',
                '2026-10-17 20:00',
                520,
                2,
                'Card',
                23200,
                4176,
                27376,
                '9104',
                'Completed',
            ),
        ]
        c.executemany(
            '''
            INSERT INTO bookings (booking_ref, customer_name, customer_phone, car_id, car_name, booking_type, pickup_location, dropoff_location, pickup_datetime, return_datetime, distance_km, days, payment_method, base_fare, tax_amount, total_fare, otp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
            bookings_data,
        )

    conn.commit()
    conn.close()


init_db()


# ==========================================
# 2. HELPER FUNCTIONS (Haversine & Maintenance)
# ==========================================
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (
        math.sin(dLat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dLon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# ==========================================
# 3. API ENDPOINTS
# ==========================================
@app.route('/api/state', methods=['GET'])
def api_state():
    conn = get_db()
    c = conn.cursor()

    cars = [dict(row) for row in c.execute('SELECT * FROM cars ORDER BY id ASC').fetchall()]
    bookings = [
        dict(row)
        for row in c.execute('SELECT * FROM bookings ORDER BY id DESC').fetchall()
    ]
    drivers = [
        dict(row)
        for row in c.execute('SELECT * FROM drivers ORDER BY id ASC').fetchall()
    ]
    settings = dict(c.execute('SELECT * FROM settings LIMIT 1').fetchone())
    user = dict(c.execute('SELECT * FROM users LIMIT 1').fetchone())

    # Predictive Maintenance AI analysis
    maintenance_alerts = []
    for car in cars:
        km_since_service = car['total_km_run'] - car['last_service_km']
        if km_since_service >= 5000:
            maintenance_alerts.append({
                'car_id': car['id'],
                'name': car['name'],
                'reg_number': car['reg_number'],
                'km_since_service': km_since_service,
                'severity': 'URGENT',
                'recommendation': 'Immediate Engine Oil, Brake Pad & Filter Overhaul Required',
            })
        elif km_since_service >= 4000:
            maintenance_alerts.append({
                'car_id': car['id'],
                'name': car['name'],
                'reg_number': car['reg_number'],
                'km_since_service': km_since_service,
                'severity': 'WARNING',
                'recommendation': 'Schedule Preventive Inspection Within 500 KM',
            })

    conn.close()
    return jsonify({
        'cars': cars,
        'bookings': bookings,
        'drivers': drivers,
        'settings': settings,
        'user': user,
        'maintenance_alerts': maintenance_alerts,
    })


@app.route('/api/book', methods=['POST'])
def api_book():
    data = request.json or {}
    conn = get_db()
    c = conn.cursor()

    car_id = int(data.get('car_id', 5))
    car = c.execute('SELECT * FROM cars WHERE id=?', (car_id,)).fetchone()
    if not car:
        conn.close()
        return jsonify({'error': 'Selected vehicle not found'}), 404

    settings = c.execute('SELECT * FROM settings LIMIT 1').fetchone()
    surge = float(settings['surge_multiplier'])

    days = max(1, int(data.get('days', 1)))
    distance_km = max(1, int(data.get('distance_km', 150)))
    booking_type = data.get('booking_type', 'Instant')
    payment_method = data.get('payment_method', 'UPI')
    customer_name = data.get('customer_name', 'Rajesh Sharma').strip() or 'Rajesh Sharma'
    customer_phone = data.get('customer_phone', '+91 98765 43210').strip() or '+91 98765 43210'
    pickup_loc = data.get('pickup_location', 'Connaught Place, New Delhi').strip() or 'Connaught Place, New Delhi'
    dropoff_loc = data.get('dropoff_location', 'IGI Airport Terminal 3').strip() or 'IGI Airport Terminal 3'

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    pickup_dt = data.get('pickup_datetime') or now_str
    return_dt = data.get('return_datetime') or now_str

    # Fare calculation
    base_car_rent = int(car['price_per_day'] * days * surge)
    distance_charge = distance_km * 12
    driver_allowance = 500 * days
    sub_total = base_car_rent + distance_charge + driver_allowance
    tax_amount = int(round(sub_total * 0.18))
    total_fare = sub_total + tax_amount

    otp = str(random.randint(1000, 9999))
    booking_ref = f"RC-{random.randint(10000, 99999)}"

    c.execute(
        '''
        INSERT INTO bookings (
            booking_ref, customer_name, customer_phone, car_id, car_name,
            booking_type, pickup_location, dropoff_location, pickup_datetime,
            return_datetime, distance_km, days, payment_method, base_fare,
            tax_amount, total_fare, otp, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active Ride')
    ''',
        (
            booking_ref,
            customer_name,
            customer_phone,
            car_id,
            car['name'],
            booking_type,
            pickup_loc,
            dropoff_loc,
            pickup_dt,
            return_dt,
            distance_km,
            days,
            payment_method,
            sub_total,
            tax_amount,
            total_fare,
            otp,
        ),
    )

    # Mark car On Trip & add loyalty points
    c.execute("UPDATE cars SET status='On Trip', total_km_run = total_km_run + ? WHERE id=?", (distance_km, car_id))
    points_earned = max(10, total_fare // 100)
    c.execute('UPDATE users SET loyalty_points = loyalty_points + ? WHERE id=1', (points_earned,))

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'booking_ref': booking_ref,
        'otp': otp,
        'car_name': car['name'],
        'driver_name': car['driver_name'],
        'total_fare': total_fare,
        'points_earned': points_earned,
    })


@app.route('/api/admin/surge', methods=['POST'])
def api_update_surge():
    data = request.json or {}
    surge = float(data.get('surge_multiplier', 1.0))
    period = data.get('active_period', 'Peak Demand')
    conn = get_db()
    conn.execute(
        'UPDATE settings SET surge_multiplier=?, active_period=? WHERE id=1',
        (surge, period),
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'surge_multiplier': surge, 'active_period': period})


@app.route('/api/admin/driver_status', methods=['POST'])
def api_driver_status():
    data = request.json or {}
    driver_id = int(data.get('driver_id', 0))
    new_status = data.get('status', 'Approved')
    conn = get_db()
    conn.execute('UPDATE drivers SET status=? WHERE id=?', (new_status, driver_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'driver_id': driver_id, 'new_status': new_status})


@app.route('/api/admin/car_status', methods=['POST'])
def api_car_status():
    data = request.json or {}
    car_id = int(data.get('car_id', 0))
    new_status = data.get('status', 'Available')
    conn = get_db()
    if new_status == 'Available':
        conn.execute(
            'UPDATE cars SET status=?, last_service_km=total_km_run WHERE id=?',
            (new_status, car_id),
        )
    else:
        conn.execute('UPDATE cars SET status=? WHERE id=?', (new_status, car_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/api/driver/respond_ride', methods=['POST'])
def api_driver_respond():
    data = request.json or {}
    action = data.get('action', 'accept')
    fare = int(data.get('fare', 450))
    conn = get_db()
    if action == 'accept':
        conn.execute(
            'UPDATE drivers SET earnings_today = earnings_today + ?, rides_completed = rides_completed + 1 WHERE id=1',
            (fare,),
        )
        conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'action': action})


@app.route('/api/refer', methods=['POST'])
def api_refer():
    data = request.json or {}
    friend_phone = (data.get('phone') or '').strip()
    if not friend_phone:
        return jsonify({'error': 'Please enter a valid mobile number'}), 400
    conn = get_db()
    conn.execute('UPDATE users SET loyalty_points = loyalty_points + 150 WHERE id=1')
    conn.commit()
    user = dict(conn.execute('SELECT * FROM users WHERE id=1').fetchone())
    conn.close()
    return jsonify({
        'status': 'success',
        'message': f'Invite sent to {friend_phone}! +150 Loyalty Points added.',
        'loyalty_points': user['loyalty_points'],
    })


@app.route('/api/estimate_route', methods=['POST'])
def api_estimate_route():
    data = request.json or {}
    lat1 = float(data.get('pickup_lat', 28.6139))
    lon1 = float(data.get('pickup_lng', 77.2090))
    lat2 = float(data.get('drop_lat', 28.5562))
    lon2 = float(data.get('drop_lng', 77.1000))

    conn = get_db()
    surge = float(conn.execute('SELECT surge_multiplier FROM settings LIMIT 1').fetchone()[0])
    conn.close()

    distance_km = max(2.5, calculate_haversine(lat1, lon1, lat2, lon2) * 1.28)
    distance_km = round(distance_km, 1)
    estimated_fare = int(round((150 + distance_km * 18) * surge))
    estimated_mins = max(8, int(round((distance_km / 38.0) * 60)))

    return jsonify({
        'distance_km': distance_km,
        'estimated_fare': estimated_fare,
        'estimated_time_mins': estimated_mins,
        'surge_multiplier': surge,
    })


@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    msg = (request.json or {}).get('message', '').lower()
    conn = get_db()
    surge = float(conn.execute('SELECT surge_multiplier FROM settings LIMIT 1').fetchone()[0])
    conn.close()

    if any(k in msg for k in ['price', 'kiraya', 'rate', 'cost', 'fare', 'tariff']):
        reply = f"RajajiCar fleet starts at ₹2,800/day for Sedans (Honda City), ₹3,200/day for EVs (Nexon EV), ₹4,000–₹5,500/day for SUVs (Thar, Fortuner), and ₹8,200–₹15,000/day for Luxury cars (BMW M3, Porsche 911). Current surge multiplier is {surge}x."
    elif any(k in msg for k in ['otp', 'pin', 'start', 'code']):
        reply = "Every confirmed booking generates a secure 4-digit Start OTP (visible in the 'Track & OTP' and 'Bookings & Loyalty' tabs). Share it only with your verified RajajiCar chauffeur when boarding."
    elif any(k in msg for k in ['cancel', 'refund']):
        reply = "You can cancel up to 1 hour before pickup for a 100% instant refund. Go to 'Bookings & Loyalty' or 'Track & OTP' to manage your active trip."
    elif any(k in msg for k in ['driver', 'track', 'location', 'where', 'kaha']):
        reply = "Open the 'Live Tracking & OTP' tab to watch your chauffeur's real-time GPS movement on our dark-mode Leaflet map along with live ETA countdown."
    elif any(k in msg for k in ['loyalty', 'point', 'refer', 'discount']):
        reply = "You earn 1 Loyalty Point for every ₹100 spent, plus 150 bonus points per friend referral! Redeem points directly for flat discounts on luxury rides."
    else:
        reply = "Namaste! Welcome to RajajiCar AI Concierge 🚗✨. Ask me about our luxury fleet prices, live GPS tracking, Ride OTP security, referral bonuses, or instant airport transfers!"

    return jsonify({'reply': reply})


# ==========================================
# 4. SINGLE-PAGE APPLICATION HTML TEMPLATE
# ==========================================
SPA_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RajajiCar — Midnight Neon Luxury Car Rental Platform</title>
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Montserrat:wght@600;700;800;900&family=Orbitron:wght@600;800&display=swap" rel="stylesheet">
  <!-- Leaflet Map CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    :root {
      --bg-dark: #0A0A0A;
      --bg-card: #141416;
      --bg-elevated: #1C1C21;
      --bg-input: #111114;
      --neon-orange: #FF5E00;
      --neon-orange-glow: rgba(255, 94, 0, 0.45);
      --neon-cyan: #00E5FF;
      --neon-green: #00FF7F;
      --neon-yellow: #FFD700;
      --neon-red: #FF3B3B;
      --text-white: #FFFFFF;
      --text-grey: #A0A5B1;
      --border-color: #2A2A32;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }
    body {
      background-color: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 85% 12%, rgba(255, 94, 0, 0.12), transparent 38%),
        radial-gradient(circle at 12% 80%, rgba(0, 229, 255, 0.06), transparent 35%);
      color: var(--text-white);
      font-family: 'Inter', sans-serif;
      line-height: 1.6;
      min-height: 100vh;
      overflow-x: hidden;
    }

    h1, h2, h3, h4, .brand-font {
      font-family: 'Montserrat', sans-serif;
      letter-spacing: -0.4px;
    }

    /* TOP STICKY GLASS NAVBAR */
    .navbar {
      position: sticky;
      top: 0;
      z-index: 1000;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 40px;
      background: rgba(10, 10, 10, 0.88);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
    }

    .logo-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      text-decoration: none;
    }

    .logo-badge {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      background: linear-gradient(135deg, #FF5E00, #FF9900);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Orbitron', sans-serif;
      font-weight: 800;
      font-size: 1.35rem;
      color: #fff;
      box-shadow: 0 0 18px var(--neon-orange-glow);
    }

    .logo-text {
      font-family: 'Orbitron', sans-serif;
      font-size: 1.35rem;
      font-weight: 800;
      color: #fff;
      letter-spacing: 1px;
    }

    .logo-text span {
      color: var(--neon-orange);
      text-shadow: 0 0 12px var(--neon-orange-glow);
    }

    .nav-pills {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      background: #121215;
      padding: 6px;
      border-radius: 12px;
      border: 1px solid var(--border-color);
    }

    .nav-pill {
      background: transparent;
      border: none;
      color: var(--text-grey);
      font-family: 'Inter', sans-serif;
      font-weight: 600;
      font-size: 0.88rem;
      padding: 9px 16px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.25s ease;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .nav-pill:hover { color: #fff; background: rgba(255, 255, 255, 0.05); }
    .nav-pill.active {
      background: var(--neon-orange);
      color: #fff;
      box-shadow: 0 0 16px var(--neon-orange-glow);
    }

    .nav-right {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .surge-pill {
      font-size: 0.8rem;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 20px;
      background: rgba(255, 94, 0, 0.14);
      border: 1px solid var(--neon-orange);
      color: var(--neon-orange);
    }

    .points-pill {
      font-size: 0.82rem;
      font-weight: 700;
      padding: 6px 13px;
      border-radius: 20px;
      background: rgba(0, 255, 127, 0.12);
      border: 1px solid var(--neon-green);
      color: var(--neon-green);
    }

    /* BUTTONS */
    .btn-neon {
      background: linear-gradient(135deg, #FF5E00, #FF8000);
      color: #fff;
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 0.92rem;
      padding: 13px 26px;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.28s ease;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .btn-neon:hover {
      box-shadow: 0 0 22px var(--neon-orange-glow), 0 0 40px rgba(255, 94, 0, 0.25);
      transform: translateY(-2px);
    }

    .btn-outline {
      background: transparent;
      color: #fff;
      border: 1px solid var(--neon-orange);
      font-family: 'Montserrat', sans-serif;
      font-weight: 700;
      font-size: 0.88rem;
      padding: 11px 20px;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.25s ease;
    }

    .btn-outline:hover {
      background: var(--neon-orange);
      box-shadow: 0 0 16px var(--neon-orange-glow);
    }

    /* VIEW SECTIONS (SPA TABS) */
    .spa-view {
      display: none;
      max-width: 1320px;
      margin: 0 auto;
      padding: 28px 32px 80px;
      animation: fadeInView 0.35s ease;
    }
    .spa-view.active { display: block; }

    @keyframes fadeInView {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* HERO SECTION */
    .hero-grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 36px;
      align-items: center;
      padding: 36px;
      background: linear-gradient(135deg, rgba(22, 22, 26, 0.95), rgba(10, 10, 12, 0.98));
      border: 1px solid var(--border-color);
      border-radius: 24px;
      position: relative;
      overflow: hidden;
      margin-bottom: 28px;
    }

    .hero-tag {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: var(--neon-orange);
      background: rgba(255, 94, 0, 0.12);
      border: 1px solid rgba(255, 94, 0, 0.35);
      padding: 6px 14px;
      border-radius: 30px;
      margin-bottom: 16px;
    }

    .hero-title {
      font-size: 3.1rem;
      font-weight: 900;
      line-height: 1.1;
      margin-bottom: 14px;
    }

    .hero-title .typewriter {
      color: var(--neon-orange);
      text-shadow: 0 0 18px rgba(255, 94, 0, 0.45);
      border-right: 3px solid var(--neon-orange);
      padding-right: 6px;
    }

    .hero-sub {
      color: var(--text-grey);
      font-size: 1.04rem;
      max-width: 540px;
      margin-bottom: 24px;
    }

    .hero-stats {
      display: flex;
      gap: 28px;
      margin-top: 26px;
      padding-top: 22px;
      border-top: 1px solid var(--border-color);
    }

    .hero-stat h3 {
      font-size: 1.65rem;
      color: var(--neon-orange);
      margin-bottom: 2px;
    }

    .hero-stat p {
      font-size: 0.8rem;
      color: var(--text-grey);
    }

    .hero-car-showcase {
      position: relative;
      text-align: center;
    }

    .hero-glow-circle {
      position: absolute;
      width: 280px;
      height: 280px;
      background: radial-gradient(circle, rgba(255, 94, 0, 0.42), transparent 70%);
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      filter: blur(25px);
      z-index: 1;
    }

    .hero-car-img {
      position: relative;
      z-index: 2;
      width: 100%;
      max-height: 310px;
      object-fit: cover;
      border-radius: 18px;
      border: 1px solid rgba(255, 94, 0, 0.4);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7);
      animation: floatCar 4s ease-in-out infinite;
    }

    @keyframes floatCar {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
    }

    /* INFINITE BRAND MARQUEE */
    .marquee-wrap {
      overflow: hidden;
      background: #111115;
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 14px 0;
      margin-bottom: 28px;
      position: relative;
    }

    .marquee-track {
      display: flex;
      gap: 44px;
      width: max-content;
      animation: scrollMarquee 24s linear infinite;
    }

    .marquee-wrap:hover .marquee-track {
      animation-play-state: paused;
    }

    .brand-chip {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 20px;
      background: #19191F;
      border: 1px solid #2C2C35;
      border-radius: 30px;
      font-family: 'Orbitron', sans-serif;
      font-size: 0.85rem;
      color: #D5D8E0;
      transition: 0.25s;
      cursor: pointer;
    }

    .brand-chip:hover {
      border-color: var(--neon-orange);
      color: var(--neon-orange);
      box-shadow: 0 0 14px rgba(255, 94, 0, 0.3);
    }

    @keyframes scrollMarquee {
      0% { transform: translateX(0); }
      100% { transform: translateX(-50%); }
    }

    /* QUICK SEARCH GLASS BAR */
    .quick-search-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      background: rgba(22, 22, 27, 0.86);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 94, 0, 0.35);
      padding: 20px;
      border-radius: 16px;
      margin-bottom: 32px;
      box-shadow: 0 14px 34px rgba(0, 0, 0, 0.55);
    }

    .field-box label {
      display: block;
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--text-grey);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .form-input, .form-select {
      width: 100%;
      background: var(--bg-input);
      border: 1px solid var(--border-color);
      color: #fff;
      padding: 11px 13px;
      border-radius: 9px;
      font-family: 'Inter', sans-serif;
      font-size: 0.92rem;
      transition: 0.25s;
    }

    .form-input:focus, .form-select:focus {
      outline: none;
      border-color: var(--neon-orange);
      box-shadow: 0 0 10px rgba(255, 94, 0, 0.3);
    }

    /* FLEET & SIDEBAR FILTER LAYOUT */
    .fleet-layout {
      display: grid;
      grid-template-columns: 270px 1fr;
      gap: 26px;
    }

    .filter-sidebar {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 22px;
      height: fit-content;
    }

    .filter-group {
      margin-bottom: 22px;
      padding-bottom: 18px;
      border-bottom: 1px solid #22222A;
    }

    .filter-group:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

    .filter-group h4 {
      color: var(--neon-orange);
      font-size: 0.88rem;
      text-transform: uppercase;
      letter-spacing: 0.7px;
      margin-bottom: 12px;
    }

    .check-label {
      display: flex;
      align-items: center;
      gap: 9px;
      color: #D0D4DC;
      font-size: 0.9rem;
      margin-bottom: 8px;
      cursor: pointer;
    }

    .check-label input {
      accent-color: var(--neon-orange);
      width: 16px;
      height: 16px;
    }

    input[type="range"] {
      width: 100%;
      accent-color: var(--neon-orange);
      cursor: pointer;
    }

    .cars-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(285px, 1fr));
      gap: 22px;
    }

    .car-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      overflow: hidden;
      transition: all 0.32s ease;
      display: flex;
      flex-direction: column;
      position: relative;
    }

    .car-card:hover {
      border-color: var(--neon-orange);
      transform: translateY(-7px);
      box-shadow: 0 14px 32px rgba(255, 94, 0, 0.16);
    }

    .car-img-wrap {
      position: relative;
      height: 185px;
      overflow: hidden;
      background: #0d0d10;
    }

    .car-img-wrap img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.45s ease;
    }

    .car-card:hover .car-img-wrap img {
      transform: scale(1.07);
    }

    .car-badge-top {
      position: absolute;
      top: 12px;
      left: 12px;
      background: rgba(10, 10, 12, 0.85);
      backdrop-filter: blur(6px);
      color: var(--neon-orange);
      border: 1px solid rgba(255, 94, 0, 0.45);
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.74rem;
      font-weight: 700;
    }

    .car-status-pill {
      position: absolute;
      top: 12px;
      right: 12px;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.72rem;
      font-weight: 700;
    }

    .status-Available { background: rgba(0, 255, 127, 0.18); color: var(--neon-green); border: 1px solid var(--neon-green); }
    .status-OnTrip { background: rgba(255, 94, 0, 0.2); color: var(--neon-orange); border: 1px solid var(--neon-orange); }
    .status-Servicing { background: rgba(255, 215, 0, 0.2); color: var(--neon-yellow); border: 1px solid var(--neon-yellow); }

    .car-body {
      padding: 18px;
      display: flex;
      flex-direction: column;
      flex: 1;
    }

    .car-title { font-size: 1.18rem; font-weight: 800; margin-bottom: 6px; }

    .car-specs {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }

    .spec-pill {
      font-size: 0.75rem;
      background: #1E1E24;
      color: var(--text-grey);
      padding: 4px 9px;
      border-radius: 6px;
    }

    .car-footer {
      margin-top: auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 12px;
      border-top: 1px solid #22222A;
    }

    .car-price {
      font-family: 'Montserrat', sans-serif;
      font-size: 1.28rem;
      font-weight: 800;
      color: var(--neon-orange);
    }

    .car-price small {
      font-size: 0.75rem;
      color: var(--text-grey);
      font-weight: 400;
    }

    /* BOOKING & FARE ESTIMATOR SPLIT */
    .booking-split {
      display: grid;
      grid-template-columns: 1.25fr 0.75fr;
      gap: 28px;
    }

    .panel-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 18px;
      padding: 26px;
    }

    .mode-tabs {
      display: flex;
      background: var(--bg-input);
      padding: 5px;
      border-radius: 12px;
      margin-bottom: 22px;
      border: 1px solid var(--border-color);
    }

    .mode-tab {
      flex: 1;
      padding: 12px;
      border: none;
      background: transparent;
      color: var(--text-grey);
      font-weight: 700;
      border-radius: 9px;
      cursor: pointer;
      transition: 0.25s;
    }

    .mode-tab.active {
      background: var(--neon-orange);
      color: #fff;
      box-shadow: 0 0 15px var(--neon-orange-glow);
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }

    .payment-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin: 14px 0 22px;
    }

    .pay-card {
      background: var(--bg-input);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 14px;
      cursor: pointer;
      transition: 0.25s;
      text-align: center;
    }

    .pay-card.active {
      border-color: var(--neon-orange);
      background: rgba(255, 94, 0, 0.1);
      box-shadow: 0 0 14px rgba(255, 94, 0, 0.22);
    }

    .receipt-box {
      background: linear-gradient(155deg, #18181D, #101014);
      border: 1px solid var(--neon-orange);
      border-radius: 18px;
      padding: 26px;
      box-shadow: 0 0 28px rgba(255, 94, 0, 0.12);
      height: fit-content;
    }

    .receipt-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 13px;
      font-size: 0.94rem;
      color: var(--text-grey);
    }

    .receipt-row strong { color: #fff; }

    .receipt-total {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-top: 1px dashed #3A3A44;
      padding-top: 16px;
      margin: 18px 0 22px;
      font-size: 1.15rem;
      font-weight: 800;
    }

    .receipt-total .grand {
      font-family: 'Montserrat', sans-serif;
      font-size: 1.75rem;
      color: var(--neon-orange);
      text-shadow: 0 0 12px var(--neon-orange-glow);
    }

    /* LIVE TRACKING & OTP */
    .tracking-grid {
      display: grid;
      grid-template-columns: 1.55fr 1fr;
      gap: 24px;
    }

    #liveMap {
      width: 100%;
      height: 520px;
      border-radius: 16px;
      border: 1px solid var(--border-color);
    }

    .otp-boxes {
      display: flex;
      justify-content: center;
      gap: 12px;
      margin: 14px 0;
    }

    .otp-digit {
      width: 52px;
      height: 60px;
      border-radius: 10px;
      background: #101014;
      border: 2px solid var(--neon-orange);
      color: var(--neon-orange);
      font-family: 'Orbitron', sans-serif;
      font-size: 1.65rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 12px rgba(255, 94, 0, 0.25);
    }

    .timeline-step {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 9px 0;
      color: var(--text-grey);
      font-size: 0.9rem;
    }

    .timeline-step.done { color: var(--neon-green); font-weight: 600; }
    .timeline-step.Current { color: var(--neon-orange); font-weight: 700; }

    /* TABLES */
    .data-table {
      width: 100%;
      border-collapse: collapse;
    }

    .data-table th, .data-table td {
      padding: 13px 14px;
      text-align: left;
      border-bottom: 1px solid #25252E;
      font-size: 0.9rem;
    }

    .data-table th {
      color: var(--text-grey);
      font-size: 0.78rem;
      text-transform: uppercase;
      background: #111115;
    }

    /* FLOATING AI CONCIERGE CHATBOT */
    .chat-fab {
      position: fixed;
      bottom: 26px;
      right: 26px;
      z-index: 2000;
      background: linear-gradient(135deg, #FF5E00, #FF8800);
      color: #fff;
      border: none;
      border-radius: 50px;
      padding: 14px 22px;
      font-family: 'Montserrat', sans-serif;
      font-weight: 800;
      font-size: 0.9rem;
      cursor: pointer;
      box-shadow: 0 8px 28px var(--neon-orange-glow);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .chat-window {
      position: fixed;
      bottom: 88px;
      right: 26px;
      width: 360px;
      background: #15151A;
      border: 1px solid var(--neon-orange);
      border-radius: 18px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
      z-index: 2000;
      display: none;
      flex-direction: column;
      overflow: hidden;
    }

    .chat-window.open { display: flex; }

    .chat-header {
      background: linear-gradient(135deg, #FF5E00, #CC4B00);
      padding: 14px 18px;
      font-weight: 800;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .chat-messages {
      height: 270px;
      overflow-y: auto;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .chat-bubble {
      padding: 10px 13px;
      border-radius: 12px;
      font-size: 0.85rem;
      max-width: 85%;
    }

    .chat-bubble.bot {
      background: #22222A;
      color: #fff;
      align-self: flex-start;
      border-bottom-left-radius: 3px;
    }

    .chat-bubble.user {
      background: var(--neon-orange);
      color: #fff;
      align-self: flex-end;
      border-bottom-right-radius: 3px;
    }

    /* SUCCESS BOOKING MODAL OVERLAY */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(8, 8, 10, 0.92);
      backdrop-filter: blur(10px);
      z-index: 3000;
      display: none;
      align-items: center;
      justify-content: center;
    }

    .modal-overlay.show { display: flex; }

    .modal-card {
      background: #16161C;
      border: 2px solid var(--neon-green);
      border-radius: 22px;
      padding: 36px;
      max-width: 460px;
      width: 92%;
      text-align: center;
      box-shadow: 0 0 40px rgba(0, 255, 127, 0.25);
    }

    @media (max-width: 980px) {
      .hero-grid, .fleet-layout, .booking-split, .tracking-grid {
        grid-template-columns: 1fr;
      }
      .navbar { padding: 12px 18px; flex-wrap: wrap; gap: 10px; }
      .hero-title { font-size: 2.2rem; }
    }
  </style>
</head>
<body>

  <!-- STICKY NAVIGATION BAR -->
  <header class="navbar">
    <a class="logo-wrap" onclick="switchView('fleet')">
      <div class="logo-badge">R</div>
      <div class="logo-text">RAJAJI<span>CAR</span></div>
    </a>

    <nav class="nav-pills">
      <button class="nav-pill active" id="nav-fleet" onclick="switchView('fleet')">🚗 Explore Fleet</button>
      <button class="nav-pill" id="nav-booking" onclick="switchView('booking')">⚡ Book & Fare Estimator</button>
      <button class="nav-pill" id="nav-tracking" onclick="switchView('tracking')">📍 Live Tracking & OTP</button>
      <button class="nav-pill" id="nav-loyalty" onclick="switchView('loyalty')">🎁 Bookings & Loyalty</button>
      <button class="nav-pill" id="nav-driver" onclick="switchView('driver')">🛞 Driver App</button>
      <button class="nav-pill" id="nav-admin" onclick="switchView('admin')">🛡️ Admin Command</button>
    </nav>

    <div class="nav-right">
      <span class="surge-pill" id="topSurgeBadge">⚡ Surge: 1.0x</span>
      <span class="points-pill" id="topPointsBadge">★ 350 Pts</span>
    </div>
  </header>

  <!-- ========================================================= -->
  <!-- VIEW 1: HERO + BRAND MARQUEE + SMART FLEET EXPLORER       -->
  <!-- ========================================================= -->
  <section class="spa-view active" id="view-fleet">
    <div class="hero-grid">
      <div>
        <div class="hero-tag">👑 India's Midnight Neon Luxury Fleet</div>
        <h1 class="hero-title">
          Rent <span class="typewriter" id="typewriterText">Luxury Cars</span><br>
          Easy, Fast & Royal
        </h1>
        <p class="hero-sub">
          Experience chauffeur-driven & self-drive executive vehicles with live GPS telemetry, transparent GST billing, instant OTP verification, and zero hidden charges.
        </p>
        <div style="display:flex; gap:14px; flex-wrap:wrap;">
          <button class="btn-neon" onclick="switchView('booking')">Book Instant Ride →</button>
          <button class="btn-outline" onclick="switchView('tracking')">View Live Ride Radar</button>
        </div>
        <div class="hero-stats">
          <div class="hero-stat"><h3>500+</h3><p>Premium Vehicles</p></div>
          <div class="hero-stat"><h3>10k+</h3><p>Verified Trips</p></div>
          <div class="hero-stat"><h3>4.9★</h3><p>Chauffeur Rating</p></div>
          <div class="hero-stat"><h3>24/7</h3><p>Roadside Concierge</p></div>
        </div>
      </div>

      <div class="hero-car-showcase">
        <div class="hero-glow-circle"></div>
        <img class="hero-car-img" src="https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80" alt="RajajiCar Hero Luxury Car">
      </div>
    </div>

    <!-- INFINITE BRAND MARQUEE -->
    <div class="marquee-wrap">
      <div class="marquee-track" id="brandMarquee">
        <span class="brand-chip" onclick="quickFilterBrand('BMW')">🔥 BMW M-SERIES</span>
        <span class="brand-chip" onclick="quickFilterBrand('Mercedes-Benz')">✨ MERCEDES-BENZ</span>
        <span class="brand-chip" onclick="quickFilterBrand('Range Rover')">👑 RANGE ROVER</span>
        <span class="brand-chip" onclick="quickFilterBrand('Porsche')">⚡ PORSCHE 911</span>
        <span class="brand-chip" onclick="quickFilterBrand('Audi')">💎 AUDI MATRIX</span>
        <span class="brand-chip" onclick="quickFilterBrand('Toyota')">🛡️ TOYOTA FORTUNER</span>
        <span class="brand-chip" onclick="quickFilterBrand('Mahindra')">🏔️ MAHINDRA THAR 4x4</span>
        <span class="brand-chip" onclick="quickFilterBrand('Tata')">🌱 TATA NEXON EV</span>
        <span class="brand-chip" onclick="quickFilterBrand('ALL')">🔄 SHOW ALL BRANDS</span>
        <!-- Duplicated for seamless marquee -->
        <span class="brand-chip" onclick="quickFilterBrand('BMW')">🔥 BMW M-SERIES</span>
        <span class="brand-chip" onclick="quickFilterBrand('Mercedes-Benz')">✨ MERCEDES-BENZ</span>
        <span class="brand-chip" onclick="quickFilterBrand('Range Rover')">👑 RANGE ROVER</span>
        <span class="brand-chip" onclick="quickFilterBrand('Porsche')">⚡ PORSCHE 911</span>
        <span class="brand-chip" onclick="quickFilterBrand('Audi')">💎 AUDI MATRIX</span>
        <span class="brand-chip" onclick="quickFilterBrand('Toyota')">🛡️ TOYOTA FORTUNER</span>
      </div>
    </div>

    <!-- QUICK SEARCH BAR -->
    <div class="quick-search-bar">
      <div class="field-box">
        <label>📍 Pick-up City / Airport</label>
        <input type="text" class="form-input" id="qsPickup" value="Connaught Place, New Delhi">
      </div>
      <div class="field-box">
        <label>🏁 Drop-off Destination</label>
        <input type="text" class="form-input" id="qsDropoff" value="IGI Airport Terminal 3">
      </div>
      <div class="field-box">
        <label>🚘 Vehicle Category</label>
        <select class="form-select" id="qsCategory" onchange="renderFleet()">
          <option value="ALL">All Categories</option>
          <option value="Luxury">Luxury & Sports</option>
          <option value="SUV">Premium SUV</option>
          <option value="Sedan">Executive Sedan</option>
        </select>
      </div>
      <div class="field-box">
        <label>🔍 Search Model or Brand</label>
        <input type="text" class="form-input" id="qsKeyword" placeholder="e.g. Fortuner, BMW, EV..." oninput="renderFleet()">
      </div>
      <div class="field-box" style="display:flex; align-items:flex-end;">
        <button class="btn-neon" style="width:100%;" onclick="document.getElementById('fleetGridAnchor').scrollIntoView({behavior:'smooth'})">Find Ride</button>
      </div>
    </div>

    <!-- FLEET FILTER SIDEBAR + INTERACTIVE GRID -->
    <div class="fleet-layout" id="fleetGridAnchor">
      <aside class="filter-sidebar">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
          <h3>Smart Filters</h3>
          <button onclick="resetFilters()" style="background:none; border:none; color:var(--neon-orange); cursor:pointer; font-size:0.8rem; font-weight:700;">Reset</button>
        </div>

        <div class="filter-group">
          <h4>Transmission</h4>
          <label class="check-label"><input type="checkbox" class="flt-trans" value="Auto" checked onchange="renderFleet()"> Automatic</label>
          <label class="check-label"><input type="checkbox" class="flt-trans" value="Manual" checked onchange="renderFleet()"> Manual</label>
        </div>

        <div class="filter-group">
          <h4>Fuel / Powertrain</h4>
          <label class="check-label"><input type="checkbox" class="flt-fuel" value="Petrol" checked onchange="renderFleet()"> Petrol</label>
          <label class="check-label"><input type="checkbox" class="flt-fuel" value="Diesel" checked onchange="renderFleet()"> Diesel</label>
          <label class="check-label"><input type="checkbox" class="flt-fuel" value="EV" checked onchange="renderFleet()"> Electric (EV)</label>
        </div>

        <div class="filter-group">
          <h4>Max Daily Tariff</h4>
          <input type="range" id="fltMaxPrice" min="2500" max="16000" step="500" value="16000" oninput="document.getElementById('fltPriceVal').textContent = this.value; renderFleet()">
          <p style="font-size:0.85rem; color:var(--text-grey); margin-top:6px;">Up to: <strong style="color:var(--neon-orange);">₹<span id="fltPriceVal">16000</span>/day</strong></p>
        </div>
      </aside>

      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
          <h2>Available Royal Fleet</h2>
          <span id="fleetCountText" style="color:var(--text-grey); font-size:0.9rem;">Showing 9 vehicles</span>
        </div>
        <div class="cars-grid" id="fleetGrid"></div>
      </div>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- VIEW 2: FLEXIBLE BOOKING + LIVE FARE ESTIMATOR            -->
  <!-- ========================================================= -->
  <section class="spa-view" id="view-booking">
    <div class="booking-split">
      <div class="panel-card">
        <h2 style="margin-bottom:6px;">Configure Your RajajiCar Booking</h2>
        <p style="color:var(--text-grey); font-size:0.9rem; margin-bottom:20px;">Switch seamlessly between Instant Chauffeur Dispatch (within 30 mins) or Scheduled Advance Trips.</p>

        <div class="mode-tabs">
          <button type="button" class="mode-tab active" id="tabInstant" onclick="setBookingMode('Instant')">⚡ Book Now (Instant Dispatch)</button>
          <button type="button" class="mode-tab" id="tabScheduled" onclick="setBookingMode('Scheduled')">📅 Schedule for Later</button>
        </div>

        <form id="mainBookingForm" onsubmit="submitBooking(event)">
          <div class="grid-2">
            <div class="field-box">
              <label>👤 Full Name</label>
              <input type="text" class="form-input" id="bkName" value="Rajesh Sharma" required>
            </div>
            <div class="field-box">
              <label>📞 Mobile Number (For SMS OTP)</label>
              <input type="tel" class="form-input" id="bkPhone" value="+91 98765 43210" required>
            </div>
          </div>

          <div class="grid-2">
            <div class="field-box">
              <label>📍 Pick-up Address</label>
              <input type="text" class="form-input" id="bkPickup" value="Connaught Place, New Delhi" required>
            </div>
            <div class="field-box">
              <label>🏁 Drop-off Destination</label>
              <input type="text" class="form-input" id="bkDropoff" value="IGI Airport Terminal 3, Delhi" required>
            </div>
          </div>

          <div id="instantNotice" style="background:rgba(255,94,0,0.12); border-left:4px solid var(--neon-orange); padding:13px 16px; border-radius:8px; margin-bottom:16px; font-size:0.9rem; color:var(--neon-orange);">
            ⚡ <strong>Instant Dispatch Active:</strong> Chauffeur will arrive at your pickup pin within 30–45 minutes.
          </div>

          <div id="scheduleFields" class="grid-2" style="display:none;">
            <div class="field-box">
              <label>📅 Pick-up Date & Time</label>
              <input type="datetime-local" class="form-input" id="bkPickupDT">
            </div>
            <div class="field-box">
              <label>📅 Return Date & Time</label>
              <input type="datetime-local" class="form-input" id="bkReturnDT">
            </div>
          </div>

          <div class="grid-2">
            <div class="field-box">
              <label>🚘 Select Fleet Vehicle</label>
              <select class="form-select" id="bkCarSelect" onchange="recalcEstimator()"></select>
            </div>
            <div class="field-box">
              <label>🛣️ Estimated Trip Distance (KM) & Days</label>
              <div style="display:flex; gap:10px;">
                <input type="number" class="form-input" id="bkDistance" value="150" min="10" max="5000" oninput="recalcEstimator()" title="Distance in KM">
                <input type="number" class="form-input" id="bkDays" value="1" min="1" max="30" oninput="recalcEstimator()" title="Number of Days">
              </div>
            </div>
          </div>

          <!-- Haversine Route Optimizer Quick Tool -->
          <div style="background:#111116; border:1px dashed #333; padding:12px 16px; border-radius:10px; margin-bottom:18px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <span style="font-size:0.83rem; color:var(--text-grey);">🗺️ Want AI Haversine Route Optimization for Delhi NCR presets?</span>
            <div style="display:flex; gap:8px;">
              <button type="button" onclick="applyRoutePreset('CP to IGI Airport', 28.6315, 77.2167, 28.5562, 77.1000)" style="background:#222; color:#fff; border:1px solid #444; padding:5px 10px; border-radius:6px; cursor:pointer; font-size:0.76rem;">CP → Airport</button>
              <button type="button" onclick="applyRoutePreset('Delhi to Agra Taj Express', 28.6139, 77.2090, 27.1767, 78.0081)" style="background:#222; color:#fff; border:1px solid #444; padding:5px 10px; border-radius:6px; cursor:pointer; font-size:0.76rem;">Delhi → Agra</button>
              <button type="button" onclick="applyRoutePreset('Gurugram to Jaipur Royal', 28.4595, 77.0266, 26.9124, 75.7873)" style="background:#222; color:#fff; border:1px solid #444; padding:5px 10px; border-radius:6px; cursor:pointer; font-size:0.76rem;">Gurugram → Jaipur</button>
            </div>
          </div>

          <label style="font-size:0.78rem; font-weight:700; color:var(--text-grey); text-transform:uppercase;">💳 Multi-Payment Gateway</label>
          <div class="payment-grid">
            <div class="pay-card active" onclick="selectPayment('UPI', this)">
              <div style="font-size:1.4rem;">📱</div>
              <div style="font-weight:700; font-size:0.9rem; margin-top:4px;">UPI Instant</div>
              <div style="font-size:0.72rem; color:var(--text-grey);">GPay / PhonePe / Paytm</div>
            </div>
            <div class="pay-card" onclick="selectPayment('Card', this)">
              <div style="font-size:1.4rem;">💳</div>
              <div style="font-weight:700; font-size:0.9rem; margin-top:4px;">Credit / Debit</div>
              <div style="font-size:0.72rem; color:var(--text-grey);">Visa / Mastercard / RuPay</div>
            </div>
            <div class="pay-card" onclick="selectPayment('Pay on Ride', this)">
              <div style="font-size:1.4rem;">💵</div>
              <div style="font-weight:700; font-size:0.9rem; margin-top:4px;">Pay on Ride</div>
              <div style="font-size:0.72rem; color:var(--text-grey);">Cash to Chauffeur</div>
            </div>
          </div>

          <button type="submit" class="btn-neon" style="width:100%; padding:16px; font-size:1.02rem;" id="bkSubmitBtn">
            ⚡ Confirm & Generate Ride OTP
          </button>
        </form>
      </div>

      <!-- RIGHT SIDE: LIVE TRANSPARENT FARE RECEIPT -->
      <div class="receipt-box">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <h3 style="color:var(--neon-orange);">Live Fare Estimator</h3>
          <span class="surge-pill" id="estSurgeTag">1.0x Surge</span>
        </div>
        <p style="font-size:0.8rem; color:var(--text-grey); margin-bottom:20px;">100% transparent breakdown inclusive of chauffeur & GST</p>

        <div class="receipt-row">
          <span>Selected Vehicle</span>
          <strong id="estCarName">Toyota Fortuner</strong>
        </div>
        <div class="receipt-row">
          <span>Base Rental (<span id="estDays">1</span> Day × Surge)</span>
          <strong>₹<span id="estBaseRent">5,500</span></strong>
        </div>
        <div class="receipt-row">
          <span>Distance Fuel Charge (<span id="estKm">150</span> km × ₹12)</span>
          <strong>₹<span id="estDistCharge">1,800</span></strong>
        </div>
        <div class="receipt-row">
          <span>Chauffeur Allowance (₹500/day)</span>
          <strong>₹<span id="estDriverAllow">500</span></strong>
        </div>
        <div class="receipt-row">
          <span>GST & State Tolls (18%)</span>
          <strong>₹<span id="estTax">1,404</span></strong>
        </div>
        <div class="receipt-row" style="color:var(--neon-green);">
          <span>🎁 Loyalty Points Earned</span>
          <strong>+<span id="estPoints">92</span> Pts</strong>
        </div>

        <div class="receipt-total">
          <span>Total Payable</span>
          <span class="grand">₹<span id="estTotal">9,204</span></span>
        </div>

        <div style="background:#121216; padding:12px; border-radius:10px; font-size:0.8rem; color:var(--text-grey);">
          🔒 <strong>RajajiCar Shield:</strong> Free cancellation up to 60 mins before pickup. Sanitized luxury cabin with chilled mineral water & Wi-Fi.
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- VIEW 3: LIVE GPS TELEMETRY TRACKING & RIDE START OTP      -->
  <!-- ========================================================= -->
  <section class="spa-view" id="view-tracking">
    <div class="tracking-grid">
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h2>Live Chauffeur Telemetry Radar</h2>
          <div style="display:flex; gap:10px;">
            <button class="btn-outline" style="padding:7px 14px; font-size:0.78rem;" onclick="restartTelemetrySim()">🔄 Replay Telemetry</button>
          </div>
        </div>
        <div id="liveMap"></div>
      </div>

      <div class="panel-card" style="display:flex; flex-direction:column; gap:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,94,0,0.12); border-left:4px solid var(--neon-orange); padding:14px 16px; border-radius:10px;">
          <div>
            <div style="font-size:0.78rem; color:var(--text-grey);">ESTIMATED CHAUFFEUR ARRIVAL</div>
            <div style="font-size:0.9rem; font-weight:700;" id="trkRouteText">Connaught Place → IGI Airport T3</div>
          </div>
          <div style="font-family:'Orbitron',sans-serif; font-size:1.45rem; font-weight:800; color:var(--neon-orange);" id="trkEtaTimer">11m 40s</div>
        </div>

        <!-- Chauffeur Card -->
        <div style="display:flex; align-items:center; gap:14px; background:#101014; padding:14px; border-radius:12px; border:1px solid var(--border-color);">
          <div style="width:54px; height:54px; border-radius:50%; background:var(--neon-orange); display:flex; align-items:center; justify-content:center; font-size:1.5rem; font-weight:800;">👮‍♂️</div>
          <div style="flex:1;">
            <h4 id="trkDriverName">Rajesh Kumar</h4>
            <p style="font-size:0.82rem; color:var(--text-grey);" id="trkCarName">⭐ 4.9 • Toyota Fortuner Legender (DL 01 AB 1234)</p>
          </div>
          <button class="btn-outline" style="padding:8px 12px; font-size:0.78rem;" onclick="alert('📞 Connecting masked call to Chauffeur (+91 98111 22334)...')">📞 Call</button>
        </div>

        <!-- 4-Digit Ride Start OTP -->
        <div style="background:#0B0B0E; border:1px dashed var(--neon-orange); border-radius:14px; padding:18px; text-align:center;">
          <div style="font-size:0.8rem; font-weight:700; text-transform:uppercase; color:var(--text-grey);">🔐 Share Ride Start OTP With Chauffeur</div>
          <div class="otp-boxes" id="trkOtpBoxes">
            <div class="otp-digit">4</div>
            <div class="otp-digit">8</div>
            <div class="otp-digit">2</div>
            <div class="otp-digit">9</div>
          </div>
          <div style="font-size:0.76rem; color:var(--text-grey);">Booking Ref: <strong style="color:#fff;" id="trkBookingRef">RC-88241</strong> • Verified Secure Trip</div>
        </div>

        <!-- Ride Progress Stepper -->
        <div>
          <h4 style="font-size:0.85rem; text-transform:uppercase; color:var(--text-grey); margin-bottom:8px;">Trip Telemetry Status</h4>
          <div class="timeline-step done">✅ Booking Confirmed & Chauffeur Assigned</div>
          <div class="timeline-step Current" id="stepEnRoute">🚗 Chauffeur En-Route to Pickup Location</div>
          <div class="timeline-step" id="stepArrived">📍 Arrived at Pickup (Waiting for OTP)</div>
          <div class="timeline-step">🏁 High-Speed Express Drop-off</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- VIEW 4: BOOKING HISTORY, GST INVOICE & LOYALTY REFERRALS  -->
  <!-- ========================================================= -->
  <section class="spa-view" id="view-loyalty">
    <div class="booking-split">
      <div class="panel-card">
        <h2 style="margin-bottom:14px;">Your Booking History & Instant Invoices</h2>
        <div id="bookingsHistoryList"></div>
      </div>

      <div style="display:flex; flex-direction:column; gap:22px;">
        <div class="receipt-box">
          <h3 style="color:var(--neon-green); margin-bottom:6px;">👑 RajajiCar Royal Club</h3>
          <p style="font-size:0.84rem; color:var(--text-grey); margin-bottom:16px;">Earn 1 Point per ₹100 spent + 150 Bonus Points for every friend you invite!</p>
          <div style="background:#101014; padding:18px; border-radius:12px; display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
            <div>
              <div style="font-size:0.76rem; color:var(--text-grey);">AVAILABLE BALANCE</div>
              <div style="font-size:2rem; font-weight:900; color:var(--neon-green);" id="loyaltyBalanceText">350 Pts</div>
            </div>
            <div style="text-align:right;">
              <div style="font-size:0.76rem; color:var(--text-grey);">VIP CODE</div>
              <div style="font-family:'Orbitron',sans-serif; font-size:1.05rem; color:var(--neon-orange);">RAJAJIVIP</div>
            </div>
          </div>

          <form onsubmit="submitReferral(event)">
            <label style="display:block; font-size:0.78rem; color:var(--text-grey); margin-bottom:6px;">INVITE A FRIEND (INSTANT +150 PTS)</label>
            <div style="display:flex; gap:10px;">
              <input type="tel" class="form-input" id="referPhoneInput" placeholder="Enter friend's mobile (+91...)" required>
              <button type="submit" class="btn-neon" style="padding:10px 18px;">Refer</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- VIEW 5: CHAUFFEUR / DRIVER MOBILE COMMAND PANEL           -->
  <!-- ========================================================= -->
  <section class="spa-view" id="view-driver">
    <div class="booking-split">
      <!--Incoming Ride Dispatch Popup-->
      <div class="panel-card" style="border-color:var(--neon-orange);">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:18px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="width:12px; height:12px; border-radius:50%; background:var(--neon-orange); display:inline-block; box-shadow:0 0 12px var(--neon-orange);"></span>
            <h3 style="color:var(--neon-orange);">Live Chauffeur Dispatch Request</h3>
          </div>
          <span class="surge-pill">Priority Airport Transfer</span>
        </div>

        <div style="background:#101014; padding:18px; border-radius:12px; margin-bottom:18px;">
          <div style="margin-bottom:12px;">
            <small style="color:var(--text-grey);">📍 PICK-UP LOCATION</small>
            <p style="font-weight:700;">The Imperial Hotel, Janpath, Connaught Place</p>
          </div>
          <div style="margin-bottom:14px;">
            <small style="color:var(--text-grey);">🏁 DROP-OFF DESTINATION</small>
            <p style="font-weight:700;">Indira Gandhi International Airport (Terminal 3)</p>
          </div>
          <div style="display:flex; justify-content:space-between; padding-top:12px; border-top:1px solid #25252E; font-size:0.92rem;">
            <span>🛣️ 18.4 km</span>
            <span>⏱️ 28 mins</span>
            <strong style="color:var(--neon-green); font-size:1.15rem;">₹850 Payout</strong>
          </div>
        </div>

        <div style="display:flex; gap:14px;">
          <button class="btn-outline" style="flex:1; border-color:var(--neon-red); color:var(--neon-red);" onclick="driverRespond('reject', 0)">✖ Reject Trip</button>
          <button class="btn-neon" style="flex:1;" onclick="driverRespond('accept', 850)">✔ Accept Ride (+₹850)</button>
        </div>
      </div>

      <!--Driver Earnings Dashboard-->
      <div class="panel-card">
        <h3 style="margin-bottom:16px;">Chauffeur Earnings & Telemetry (Rajesh Kumar)</h3>
        <div style="background:linear-gradient(135deg, #FF5E00, #B84000); padding:22px; border-radius:16px; margin-bottom:18px;">
          <div style="font-size:0.85rem; opacity:0.9;">TODAY'S VERIFIED PAYOUT</div>
          <div style="font-size:2.4rem; font-weight:900; font-family:'Montserrat',sans-serif;" id="drvEarnings">₹2,450</div>
          <div style="font-size:0.8rem; margin-top:4px;">↑ 18% higher than daily fleet average</div>
        </div>

        <div class="grid-2">
          <div style="background:#101014; padding:16px; border-radius:12px; text-align:center;">
            <div style="font-size:1.6rem; font-weight:800; color:var(--neon-orange);" id="drvRidesCount">12</div>
            <div style="font-size:0.8rem; color:var(--text-grey);">Rides Completed</div>
          </div>
          <div style="background:#101014; padding:16px; border-radius:12px; text-align:center;">
            <div style="font-size:1.6rem; font-weight:800; color:var(--neon-green);">6.5 hrs</div>
            <div style="font-size:0.8rem; color:var(--text-grey);">Active Online Shift</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- VIEW 6: ADMIN COMMAND CENTER (FLEET, DRIVERS, SURGE, AI)  -->
  <!-- ========================================================= -->
  <section class="spa-view" id="view-admin">
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:18px; margin-bottom:26px;">
      <div class="panel-card" style="border-left:4px solid var(--neon-green);">
        <div style="font-size:0.8rem; color:var(--text-grey);">AVAILABLE FLEET</div>
        <div style="font-size:2rem; font-weight:900;" id="admIdleCount">7</div>
      </div>
      <div class="panel-card" style="border-left:4px solid var(--neon-orange);">
        <div style="font-size:0.8rem; color:var(--text-grey);">ACTIVE ON-TRIP</div>
        <div style="font-size:2rem; font-weight:900;" id="admActiveCount">1</div>
      </div>
      <div class="panel-card" style="border-left:4px solid var(--neon-yellow);">
        <div style="font-size:0.8rem; color:var(--text-grey);">IN SERVICE BAY</div>
        <div style="font-size:2rem; font-weight:900;" id="admServiceCount">1</div>
      </div>
      <div class="panel-card" style="border-left:4px solid var(--neon-cyan);">
        <div style="font-size:0.8rem; color:var(--text-grey);">ACTIVE SURGE</div>
        <div style="font-size:2rem; font-weight:900; color:var(--neon-orange);" id="admSurgeStat">1.0x</div>
      </div>
    </div>

    <div class="booking-split" style="margin-bottom:26px;">
      <!-- Dynamic Surge Pricing Control -->
      <div class="panel-card">
        <h3 style="margin-bottom:8px;">⚡ Dynamic Surge Pricing Controller</h3>
        <p style="font-size:0.85rem; color:var(--text-grey); margin-bottom:18px;">Adjust real-time multiplier across all customer fare estimators.</p>
        <div class="field-box" style="margin-bottom:16px;">
          <label>Surge Multiplier: <strong style="color:var(--neon-orange); font-size:1.15rem;" id="admSurgeLabel">1.0x</strong></label>
          <input type="range" min="1.0" max="3.0" step="0.1" value="1.0" id="admSurgeSlider" oninput="document.getElementById('admSurgeLabel').textContent = parseFloat(this.value).toFixed(1) + 'x'">
        </div>
        <div class="field-box" style="margin-bottom:18px;">
          <label>Active Tariff Window</label>
          <select class="form-select" id="admSurgePeriod">
            <option value="Normal Hours (1.0x)">Normal Hours</option>
            <option value="Peak Rush / Night Hours">Peak Rush / Night Hours (10 PM - 6 AM)</option>
            <option value="Weekend Royal Demand">Weekend Royal Demand (Sat - Sun)</option>
            <option value="Festival / Wedding Season">Festival & Wedding Season</option>
          </select>
        </div>
        <button class="btn-neon" onclick="updateAdminSurge()">Broadcast Surge Pricing</button>
      </div>

      <!-- AI Predictive Maintenance Alerts -->
      <div class="panel-card">
        <h3 style="margin-bottom:8px;">🔧 AI Predictive Maintenance Engine</h3>
        <p style="font-size:0.85rem; color:var(--text-grey); margin-bottom:14px;">Automated telemetry alerts for vehicles exceeding 4,000+ KM since last overhaul.</p>
        <div id="admMaintenanceList"></div>
      </div>
    </div>

    <!-- Driver KYC & Approvals -->
    <div class="panel-card" style="margin-bottom:26px;">
      <h3 style="margin-bottom:14px;">👮‍♂️ Chauffeur Onboarding & KYC Verification</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Chauffeur Name</th>
            <th>Phone</th>
            <th>Assigned Vehicle</th>
            <th>Driving License & KYC</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="admDriversTable"></tbody>
      </table>
    </div>

    <!-- Fleet Status Management -->
    <div class="panel-card">
      <h3 style="margin-bottom:14px;">🚘 Live Fleet Status & Bay Controller</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Vehicle</th>
            <th>Registration</th>
            <th>Chauffeur</th>
            <th>Odometer (KM)</th>
            <th>Status</th>
            <th>Quick Dispatch / Service</th>
          </tr>
        </thead>
        <tbody id="admFleetTable"></tbody>
      </table>
    </div>
  </section>

  <!-- ========================================================= -->
  <!-- BOOKING CONFIRMATION ANIMATED MODAL                       -->
  <!-- ========================================================= -->
  <div class="modal-overlay" id="bookingSuccessModal">
    <div class="modal-card">
      <div style="font-size:3.4rem; margin-bottom:10px;">🚗💨 ✅</div>
      <h2 style="color:var(--neon-green); margin-bottom:8px;">Booking Confirmed!</h2>
      <p style="color:var(--text-grey); font-size:0.92rem; margin-bottom:18px;" id="modalSummaryText"></p>
      <div style="background:#0D0D11; border:1px dashed var(--neon-orange); padding:14px; border-radius:12px; margin-bottom:20px;">
        <div style="font-size:0.75rem; color:var(--text-grey);">YOUR RIDE START OTP</div>
        <div style="font-family:'Orbitron',sans-serif; font-size:2rem; font-weight:800; color:var(--neon-orange); letter-spacing:6px;" id="modalOtpText">4829</div>
      </div>
      <button class="btn-neon" style="width:100%;" onclick="closeModalAndTrack()">Open Live Chauffeur Radar →</button>
    </div>
  </div>

  <!-- ========================================================= -->
  <!-- FLOATING AI CONCIERGE WIDGET                              -->
  <!-- ========================================================= -->
  <button class="chat-fab" onclick="toggleChat()">🤖 RajajiCar AI Concierge</button>
  <div class="chat-window" id="chatWindow">
    <div class="chat-header">
      <span>🤖 RajajiCar AI Support</span>
      <button onclick="toggleChat()" style="background:none; border:none; color:#fff; font-size:1.1rem; cursor:pointer;">✖</button>
    </div>
    <div class="chat-messages" id="chatMessages">
      <div class="chat-bubble bot">Namaste! 👋 Welcome to RajajiCar Midnight Neon Concierge. Ask me about car prices, Ride OTP, live tracking, or loyalty points!</div>
    </div>
    <form onsubmit="sendChatMessage(event)" style="display:flex; border-top:1px solid #2A2A32;">
      <input type="text" id="chatInput" placeholder="Ask about prices, OTP, refund..." style="flex:1; background:#0E0E12; border:none; color:#fff; padding:12px; outline:none;">
      <button type="submit" style="background:var(--neon-orange); color:#fff; border:none; padding:0 16px; font-weight:700; cursor:pointer;">Send</button>
    </form>
  </div>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    let APP_STATE = {
      cars: [],
      bookings: [],
      drivers: [],
      settings: { surge_multiplier: 1.0, active_period: 'Normal Hours' },
      user: { loyalty_points: 350 },
      maintenance_alerts: []
    };

    let selectedBookingMode = 'Instant';
    let selectedPaymentMethod = 'UPI';
    let selectedBrandFilter = 'ALL';

    // Typewriter Hero Animation
    const heroPhrases = ['Luxury Cars', 'Executive SUVs', 'Electric Rides', 'Sports Coupes'];
    let phraseIdx = 0;
    setInterval(() => {
      phraseIdx = (phraseIdx + 1) % heroPhrases.length;
      const el = document.getElementById('typewriterText');
      if (el) el.textContent = heroPhrases[phraseIdx];
    }, 2600);

    // Switch SPA Views
    function switchView(viewName) {
      document.querySelectorAll('.spa-view').forEach(v => v.classList.remove('active'));
      document.querySelectorAll('.nav-pill').forEach(b => b.classList.remove('active'));
      const targetView = document.getElementById('view-' + viewName);
      const targetNav = document.getElementById('nav-' + viewName);
      if (targetView) targetView.classList.add('active');
      if (targetNav) targetNav.classList.add('active');

      if (viewName === 'tracking') {
        setTimeout(() => {
          initOrRefreshMap();
        }, 150);
      }
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Load Full State from Backend
    async function fetchAppState() {
      const res = await fetch('/api/state');
      APP_STATE = await res.json();
      updateTopBadges();
      renderFleet();
      populateBookingDropdown();
      recalcEstimator();
      renderBookingsHistory();
      renderAdminPanel();
    }

    function updateTopBadges() {
      const surge = parseFloat(APP_STATE.settings.surge_multiplier || 1.0).toFixed(1);
      document.getElementById('topSurgeBadge').textContent = `⚡ Surge: ${surge}x`;
      document.getElementById('estSurgeTag').textContent = `${surge}x Surge`;
      document.getElementById('topPointsBadge').textContent = `★ ${APP_STATE.user.loyalty_points} Pts`;
      document.getElementById('loyaltyBalanceText').textContent = `${APP_STATE.user.loyalty_points} Pts`;
    }

    function quickFilterBrand(brand) {
      selectedBrandFilter = brand;
      renderFleet();
      document.getElementById('fleetGridAnchor').scrollIntoView({ behavior: 'smooth' });
    }

    function resetFilters() {
      selectedBrandFilter = 'ALL';
      document.getElementById('qsCategory').value = 'ALL';
      document.getElementById('qsKeyword').value = '';
      document.getElementById('fltMaxPrice').value = 16000;
      document.getElementById('fltPriceVal').textContent = '16000';
      document.querySelectorAll('.flt-trans, .flt-fuel').forEach(cb => cb.checked = true);
      renderFleet();
    }

    function renderFleet() {
      const category = document.getElementById('qsCategory').value;
      const keyword = document.getElementById('qsKeyword').value.toLowerCase().trim();
      const maxPrice = parseInt(document.getElementById('fltMaxPrice').value, 10);
      const allowedTrans = Array.from(document.querySelectorAll('.flt-trans:checked')).map(c => c.value);
      const allowedFuel = Array.from(document.querySelectorAll('.flt-fuel:checked')).map(c => c.value);

      const filtered = APP_STATE.cars.filter(car => {
        if (selectedBrandFilter !== 'ALL' && car.brand !== selectedBrandFilter) return false;
        if (category !== 'ALL' && car.category !== category) return false;
        if (keyword && !(car.name.toLowerCase().includes(keyword) || car.brand.toLowerCase().includes(keyword))) return false;
        if (car.price_per_day > maxPrice) return false;
        if (!allowedTrans.includes(car.transmission)) return false;
        if (!allowedFuel.includes(car.fuel)) return false;
        return true;
      });

      document.getElementById('fleetCountText').textContent = `Showing ${filtered.length} vehicles`;
      const grid = document.getElementById('fleetGrid');
      if (filtered.length === 0) {
        grid.innerHTML = `<div class="panel-card" style="grid-column:1/-1; text-align:center; padding:40px;">
          <h3 style="color:var(--neon-orange);">No Matching Vehicles Found</h3>
          <p style="color:var(--text-grey); margin:10px 0 18px;">Try expanding your price range or resetting brand filters.</p>
          <button class="btn-outline" onclick="resetFilters()">Reset All Filters</button>
        </div>`;
        return;
      }

      grid.innerHTML = filtered.map(car => {
        const statusCls = 'status-' + car.status.replace(/\s+/g, '');
        return `
          <div class="car-card">
            <div class="car-img-wrap">
              <img src="${car.image_url}" alt="${car.name}">
              <span class="car-badge-top">${car.brand} • ${car.category}</span>
              <span class="car-status-pill ${statusCls}">${car.status}</span>
            </div>
            <div class="car-body">
              <div class="car-title">${car.name}</div>
              <div class="car-specs">
                <span class="spec-pill">⚙️ ${car.transmission}</span>
                <span class="spec-pill">⛽ ${car.fuel}</span>
                <span class="spec-pill">💺 ${car.seats} Seats</span>
                <span class="spec-pill">🔥 ${car.hp}</span>
              </div>
              <div style="font-size:0.78rem; color:var(--text-grey); margin-bottom:12px;">
                👮‍♂️ Chauffeur: <strong style="color:#fff;">${car.driver_name}</strong> (${car.reg_number})
              </div>
              <div class="car-footer">
                <div class="car-price">₹${car.price_per_day.toLocaleString('en-IN')} <small>/ day</small></div>
                <button class="btn-neon" style="padding:9px 16px; font-size:0.8rem;" onclick="selectCarForBooking(${car.id})">
                  Select Ride →
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function selectCarForBooking(carId) {
      const sel = document.getElementById('bkCarSelect');
      if (sel) sel.value = String(carId);
      document.getElementById('bkPickup').value = document.getElementById('qsPickup').value;
      document.getElementById('bkDropoff').value = document.getElementById('qsDropoff').value;
      recalcEstimator();
      switchView('booking');
    }

    function populateBookingDropdown() {
      const sel = document.getElementById('bkCarSelect');
      const currentVal = sel.value;
      sel.innerHTML = APP_STATE.cars.map(c =>
        `<option value="${c.id}">${c.name} — ₹${c.price_per_day.toLocaleString('en-IN')}/day (${c.transmission} • ${c.fuel})</option>`
      ).join('');
      if (currentVal) sel.value = currentVal;
    }

    function setBookingMode(mode) {
      selectedBookingMode = mode;
      document.getElementById('tabInstant').classList.toggle('active', mode === 'Instant');
      document.getElementById('tabScheduled').classList.toggle('active', mode === 'Scheduled');
      document.getElementById('instantNotice').style.display = mode === 'Instant' ? 'block' : 'none';
      document.getElementById('scheduleFields').style.display = mode === 'Scheduled' ? 'grid' : 'none';
    }

    function selectPayment(method, cardEl) {
      selectedPaymentMethod = method;
      document.querySelectorAll('.pay-card').forEach(el => el.classList.remove('active'));
      cardEl.classList.add('active');
    }

    function recalcEstimator() {
      const carId = parseInt(document.getElementById('bkCarSelect').value || '1', 10);
      const car = APP_STATE.cars.find(c => c.id === carId) || APP_STATE.cars[0];
      if (!car) return;

      const days = Math.max(1, parseInt(document.getElementById('bkDays').value || '1', 10));
      const km = Math.max(1, parseInt(document.getElementById('bkDistance').value || '150', 10));
      const surge = parseFloat(APP_STATE.settings.surge_multiplier || 1.0);

      const baseRent = Math.round(car.price_per_day * days * surge);
      const distCharge = km * 12;
      const driverAllow = 500 * days;
      const subTotal = baseRent + distCharge + driverAllow;
      const tax = Math.round(subTotal * 0.18);
      const grandTotal = subTotal + tax;
      const points = Math.max(10, Math.floor(grandTotal / 100));

      document.getElementById('estCarName').textContent = car.name;
      document.getElementById('estDays').textContent = days;
      document.getElementById('estKm').textContent = km;
      document.getElementById('estBaseRent').textContent = baseRent.toLocaleString('en-IN');
      document.getElementById('estDistCharge').textContent = distCharge.toLocaleString('en-IN');
      document.getElementById('estDriverAllow').textContent = driverAllow.toLocaleString('en-IN');
      document.getElementById('estTax').textContent = tax.toLocaleString('en-IN');
      document.getElementById('estPoints').textContent = points;
      document.getElementById('estTotal').textContent = grandTotal.toLocaleString('en-IN');
    }

    async function applyRoutePreset(title, lat1, lng1, lat2, lng2) {
      const res = await fetch('/api/estimate_route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pickup_lat: lat1, pickup_lng: lng1, drop_lat: lat2, drop_lng: lng2 })
      });
      const data = await res.json();
      const parts = title.split(' to ');
      if (parts.length === 2) {
        document.getElementById('bkPickup').value = parts[0];
        document.getElementById('bkDropoff').value = parts[1];
      }
      document.getElementById('bkDistance').value = Math.round(data.distance_km);
      recalcEstimator();
    }

    async function submitBooking(e) {
      e.preventDefault();
      const payload = {
        customer_name: document.getElementById('bkName').value,
        customer_phone: document.getElementById('bkPhone').value,
        pickup_location: document.getElementById('bkPickup').value,
        dropoff_location: document.getElementById('bkDropoff').value,
        car_id: parseInt(document.getElementById('bkCarSelect').value, 10),
        distance_km: parseInt(document.getElementById('bkDistance').value, 10),
        days: parseInt(document.getElementById('bkDays').value, 10),
        booking_type: selectedBookingMode,
        payment_method: selectedPaymentMethod,
        pickup_datetime: document.getElementById('bkPickupDT').value,
        return_datetime: document.getElementById('bkReturnDT').value
      };

      const res = await fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const out = await res.json();
      if (out.status === 'success') {
        document.getElementById('modalSummaryText').textContent =
          `${out.car_name} assigned with chauffeur ${out.driver_name}. Total Fare ₹${out.total_fare.toLocaleString('en-IN')} (+${out.points_earned} Loyalty Points added!).`;
        document.getElementById('modalOtpText').textContent = out.otp;

        // Update Live Tracking Panel with this latest booking
        document.getElementById('trkDriverName').textContent = out.driver_name;
        document.getElementById('trkCarName').textContent = `⭐ 4.9 • ${out.car_name}`;
        document.getElementById('trkBookingRef').textContent = out.booking_ref;
        document.getElementById('trkRouteText').textContent = `${payload.pickup_location} → ${payload.dropoff_location}`;
        document.getElementById('trkOtpBoxes').innerHTML = out.otp.split('').map(d => `<div class="otp-digit">${d}</div>`).join('');

        document.getElementById('bookingSuccessModal').classList.add('show');
        await fetchAppState();
      }
    }

    function closeModalAndTrack() {
      document.getElementById('bookingSuccessModal').classList.remove('show');
      switchView('tracking');
    }

    // LEAFLET DARK TELEMETRY MAP
    let leafletMap = null;
    let driverMarker = null;
    let simInterval = null;
    const userCoords = [28.6139, 77.2090];
    const driverStartCoords = [28.6325, 77.2240];

    function initOrRefreshMap() {
      if (!leafletMap) {
        leafletMap = L.map('liveMap').setView(userCoords, 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; OpenStreetMap &copy; CartoDB',
          maxZoom: 19
        }).addTo(leafletMap);

        const userIcon = L.divIcon({
          className: '',
          html: `<div style="width:18px;height:18px;border-radius:50%;background:#FF5E00;border:3px solid #fff;box-shadow:0 0 14px #FF5E00;"></div>`,
          iconSize: [18, 18]
        });

        const carIcon = L.divIcon({
          className: '',
          html: `<div style="font-size:26px;filter:drop-shadow(0 0 8px #FF5E00);">🚗</div>`,
          iconSize: [30, 30]
        });

        L.marker(userCoords, { icon: userIcon }).addTo(leafletMap).bindPopup('📍 Your Pickup Location');
        driverMarker = L.marker(driverStartCoords, { icon: carIcon }).addTo(leafletMap).bindPopup('👮‍♂️ RajajiCar Chauffeur');

        const routeLine = L.polyline([driverStartCoords, userCoords], {
          color: '#FF5E00',
          weight: 4,
          dashArray: '10, 10'
        }).addTo(leafletMap);

        leafletMap.fitBounds(routeLine.getBounds(), { padding: [45, 45] });
        restartTelemetrySim();
      } else {
        leafletMap.invalidateSize();
      }
    }

    function restartTelemetrySim() {
      if (simInterval) clearInterval(simInterval);
      let step = 0;
      const totalSteps = 60;
      let etaSecs = 11 * 60 + 40;
      document.getElementById('stepEnRoute').className = 'timeline-step Current';
      document.getElementById('stepArrived').className = 'timeline-step';

      simInterval = setInterval(() => {
        step++;
        const lat = driverStartCoords[0] + ((userCoords[0] - driverStartCoords[0]) * (step / totalSteps));
        const lng = driverStartCoords[1] + ((userCoords[1] - driverStartCoords[1]) * (step / totalSteps));
        if (driverMarker) driverMarker.setLatLng([lat, lng]);

        etaSecs = Math.max(0, etaSecs - 11);
        const mins = Math.floor(etaSecs / 60);
        const secs = etaSecs % 60;
        const timerEl = document.getElementById('trkEtaTimer');

        if (step >= totalSteps) {
          clearInterval(simInterval);
          if (timerEl) timerEl.textContent = 'ARRIVED 📍';
          document.getElementById('stepEnRoute').className = 'timeline-step done';
          document.getElementById('stepArrived').className = 'timeline-step Current';
        } else {
          if (timerEl) timerEl.textContent = `${mins}m ${secs}s`;
        }
      }, 900);
    }

    // BOOKING HISTORY & PRINTABLE GST INVOICE
    function renderBookingsHistory() {
      const wrap = document.getElementById('bookingsHistoryList');
      wrap.innerHTML = APP_STATE.bookings.map(b => `
        <div style="background:#101014; border-left:4px solid var(--neon-orange); padding:16px; border-radius:10px; margin-bottom:14px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
          <div>
            <div style="display:flex; align-items:center; gap:10px;">
              <h4 style="margin:0;">${b.car_name}</h4>
              <span class="surge-pill" style="font-size:0.72rem;">${b.booking_ref}</span>
            </div>
            <p style="font-size:0.83rem; color:var(--text-grey); margin:4px 0;">
              📍 ${b.pickup_location} → ${b.dropoff_location} (${b.distance_km} KM • ${b.days} Day)
            </p>
            <p style="font-size:0.78rem; color:var(--text-grey);">
              💳 ${b.payment_method} • 🔐 OTP: <strong style="color:var(--neon-orange);">${b.otp}</strong> • Status: <strong style="color:var(--neon-green);">${b.status}</strong>
            </p>
          </div>
          <div style="text-align:right;">
            <div style="font-size:1.25rem; font-weight:800; color:var(--neon-orange); margin-bottom:6px;">₹${b.total_fare.toLocaleString('en-IN')}</div>
            <button class="btn-outline" style="padding:6px 12px; font-size:0.76rem;" onclick='downloadGSTInvoice(${JSON.stringify(b)})'>📥 GST Invoice</button>
          </div>
        </div>
      `).join('');
    }

    function downloadGSTInvoice(b) {
      const win = window.open('', '_blank', 'width=720,height=680');
      win.document.write(`
        <html><head><title>RajajiCar GST Invoice - ${b.booking_ref}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 36px; color: #111; }
          .head { display: flex; justify-content: space-between; border-bottom: 3px solid #FF5E00; padding-bottom: 16px; }
          table { width: 100%; border-collapse: collapse; margin-top: 24px; }
          th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
          th { background: #f5f5f5; }
        </style></head><body>
          <div class="head">
            <div><h1 style="margin:0;color:#FF5E00;">RAJAJICAR</h1><p>Midnight Neon Luxury Mobility Pvt. Ltd.<br>GSTIN: 07AABCR8821K1Z5</p></div>
            <div style="text-align:right;"><h3>TAX INVOICE</h3><p>Invoice #: <strong>${b.booking_ref}</strong><br>Date: ${b.pickup_datetime}</p></div>
          </div>
          <p style="margin-top:20px;"><strong>Billed To:</strong> ${b.customer_name} (${b.customer_phone})<br>
          <strong>Route:</strong> ${b.pickup_location} to ${b.dropoff_location}</p>
          <table>
            <tr><th>Description</th><th>Qty / Distance</th><th>Amount (INR)</th></tr>
            <tr><td>${b.car_name} (${b.booking_type} Booking + Chauffeur)</td><td>${b.days} Day(s) / ${b.distance_km} KM</td><td>₹${b.base_fare.toLocaleString('en-IN')}</td></tr>
            <tr><td>IGST / CGST + State Highway Taxes (18%)</td><td>18%</td><td>₹${b.tax_amount.toLocaleString('en-IN')}</td></tr>
            <tr><th colspan="2">Grand Total Paid via ${b.payment_method}</th><th>₹${b.total_fare.toLocaleString('en-IN')}</th></tr>
          </table>
          <p style="margin-top:30px;font-size:12px;color:#555;">Computer generated GST invoice. Ride Start OTP Verified: ${b.otp}</p>
          <script>window.print();<\/script>
        </body></html>
      `);
      win.document.close();
    }

    async function submitReferral(e) {
      e.preventDefault();
      const phone = document.getElementById('referPhoneInput').value;
      const res = await fetch('/api/refer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      });
      const out = await res.json();
      if (out.status === 'success') {
        alert(out.message);
        document.getElementById('referPhoneInput').value = '';
        await fetchAppState();
      }
    }

    async function driverRespond(action, fare) {
      await fetch('/api/driver/respond_ride', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, fare })
      });
      await fetchAppState();
      const d1 = APP_STATE.drivers[0];
      if (d1) {
        document.getElementById('drvEarnings').textContent = '₹' + d1.earnings_today.toLocaleString('en-IN');
        document.getElementById('drvRidesCount').textContent = d1.rides_completed;
      }
      alert(action === 'accept' ? '✅ Ride Accepted! Navigation started & ₹850 added to today\'s payout.' : '⚠️ Ride request passed to next chauffeur.');
    }

    // ADMIN PANEL RENDERING
    function renderAdminPanel() {
      const idle = APP_STATE.cars.filter(c => c.status === 'Available').length;
      const active = APP_STATE.cars.filter(c => c.status === 'On Trip').length;
      const service = APP_STATE.cars.filter(c => c.status === 'Servicing').length;

      document.getElementById('admIdleCount').textContent = idle;
      document.getElementById('admActiveCount').textContent = active;
      document.getElementById('admServiceCount').textContent = service;
      document.getElementById('admSurgeStat').textContent = parseFloat(APP_STATE.settings.surge_multiplier).toFixed(1) + 'x';

      // Maintenance List
      const maintEl = document.getElementById('admMaintenanceList');
      if (APP_STATE.maintenance_alerts.length === 0) {
        maintEl.innerHTML = `<div style="color:var(--neon-green);">✅ All fleet vehicles are within healthy service intervals.</div>`;
      } else {
        maintEl.innerHTML = APP_STATE.maintenance_alerts.map(a => `
          <div style="background:#101014; border-left:4px solid ${a.severity === 'URGENT' ? 'var(--neon-red)' : 'var(--neon-yellow)'}; padding:10px 14px; border-radius:8px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <strong style="color:#fff;">${a.name} (${a.reg_number})</strong>
              <div style="font-size:0.78rem; color:var(--text-grey);">${a.km_since_service} KM since last service • ${a.recommendation}</div>
            </div>
            <span class="surge-pill" style="font-size:0.7rem;">${a.severity}</span>
          </div>
        `).join('');
      }

      // Drivers KYC Table
      document.getElementById('admDriversTable').innerHTML = APP_STATE.drivers.map(d => `
        <tr>
          <td><strong>${d.name}</strong> (⭐ ${d.rating})</td>
          <td>${d.phone}</td>
          <td>${d.car_model} (${d.reg_number})</td>
          <td><span style="color:var(--neon-orange);">📄 ${d.license_no}</span> • Aadhar Verified</td>
          <td><strong style="color:${d.status === 'Approved' ? 'var(--neon-green)' : 'var(--neon-yellow)'};">${d.status}</strong></td>
          <td>
            <button class="btn-outline" style="padding:5px 10px; font-size:0.74rem; border-color:var(--neon-green); color:var(--neon-green);" onclick="setDriverStatus(${d.id}, 'Approved')">✔ Approve</button>
            <button class="btn-outline" style="padding:5px 10px; font-size:0.74rem; border-color:var(--neon-red); color:var(--neon-red);" onclick="setDriverStatus(${d.id}, 'Blocked')">✖ Block</button>
          </td>
        </tr>
      `).join('');

      // Fleet Bay Table
      document.getElementById('admFleetTable').innerHTML = APP_STATE.cars.map(c => `
        <tr>
          <td><strong>${c.name}</strong></td>
          <td>${c.reg_number}</td>
          <td>${c.driver_name}</td>
          <td>${c.total_km_run.toLocaleString('en-IN')} KM</td>
          <td><span class="car-status-pill status-${c.status.replace(/\s+/g, '')}" style="position:static;">${c.status}</span></td>
          <td>
            <button class="btn-outline" style="padding:5px 10px; font-size:0.74rem;" onclick="setCarStatus(${c.id}, 'Available')">Set Available</button>
            <button class="btn-outline" style="padding:5px 10px; font-size:0.74rem;" onclick="setCarStatus(${c.id}, 'Servicing')">Send to Service</button>
          </td>
        </tr>
      `).join('');
    }

    async function updateAdminSurge() {
      const surge = parseFloat(document.getElementById('admSurgeSlider').value);
      const period = document.getElementById('admSurgePeriod').value;
      await fetch('/api/admin/surge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ surge_multiplier: surge, active_period: period })
      });
      await fetchAppState();
      alert(`⚡ Dynamic Surge updated to ${surge.toFixed(1)}x (${period}) across the platform!`);
    }

    async function setDriverStatus(driverId, status) {
      await fetch('/api/admin/driver_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ driver_id: driverId, status })
      });
      await fetchAppState();
    }

    async function setCarStatus(carId, status) {
      await fetch('/api/admin/car_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ car_id: carId, status })
      });
      await fetchAppState();
    }

    // AI CONCIERGE CHATBOT
    function toggleChat() {
      document.getElementById('chatWindow').classList.toggle('open');
    }

    async function sendChatMessage(e) {
      e.preventDefault();
      const input = document.getElementById('chatInput');
      const text = input.value.trim();
      if (!text) return;

      const box = document.getElementById('chatMessages');
      box.innerHTML += `<div class="chat-bubble user">${text}</div>`;
      input.value = '';
      box.scrollTop = box.scrollHeight;

      const res = await fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();
      box.innerHTML += `<div class="chat-bubble bot">${data.reply}</div>`;
      box.scrollTop = box.scrollHeight;
    }

    // Initialize on load
    document.addEventListener('DOMContentLoaded', fetchAppState);
  </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(SPA_HTML)


if __name__ == '__main__':
    print('🚗 RajajiCar Single-File Full-Stack Platform running on http://127.0.0.1:5000')
    app.run(host='0.0.0.0', port=5000, debug=True)
