import os
import django
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'piba.settings')
django.setup()

import urllib.request
import urllib.error
import urllib.parse
from users.models import User
from sellers.models import SellerProfile
from pets.models import Pet, PetCategory
from orders.models import Order

BASE_URL = 'http://localhost:8000'

def make_request(method, path, data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req_headers = {'Content-Type': 'application/json'}
    if headers:
        req_headers.update(headers)
    
    req_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))

def run_tests():
    print("Setting up test data...")
    # Clean up previous test data if exists
    Order.objects.filter(buyer__email='test_buyer@abc.com').delete()
    User.objects.filter(email__in=['test_buyer@abc.com', 'test_seller@abc.com', 'admin@abc.com']).delete()
    
    admin = User.objects.create_superuser(email='admin@abc.com', username='admin_test', password='password123')
    
    buyer = User.objects.create_user(email='test_buyer@abc.com', username='test_buyer', password='password123', role='buyer')
    
    seller = User.objects.create_user(email='test_seller@abc.com', username='test_seller', password='password123', role='seller')
    seller_profile = SellerProfile.objects.create(user=seller, business_name='Test Shop', is_verified=True)
    
    cat, _ = PetCategory.objects.get_or_create(name='Dogs', slug='dogs')
    pet = Pet.objects.create(name='Test Dog', category=cat, seller=seller_profile, price=1000, status='available')
    
    order = Order.objects.create(
        buyer=buyer,
        seller=seller_profile,
        subtotal=1000,
        tax_amount=180,
        total_amount=1180,
        payment_method='cod',
        status='pending'
    )
    
    print("\n--- Test 1: Deactivated User Login ---")
    buyer.is_active = False
    buyer.save()
    
    status_code, response_json = make_request('POST', '/api/v1/auth/login/', data={'email': 'test_buyer@abc.com', 'password': 'password123'})
    print(f"Status: {status_code}")
    print(f"Response: {response_json}")
    assert status_code == 400
    assert 'Your account has been deactivated.' in str(response_json)
    print("Test 1 PASS")
    
    print("\n--- Test 2: Unverified Seller Login ---")
    seller_profile.is_verified = False
    seller_profile.save()
    
    status_code, response_json = make_request('POST', '/api/v1/auth/login/', data={'email': 'test_seller@abc.com', 'password': 'password123'})
    print(f"Status: {status_code}")
    print(f"Response: {response_json}")
    assert status_code == 400
    assert 'Your shop verification has been revoked.' in str(response_json)
    print("Test 2 PASS")
    
    print("\n--- Test 3: Auto-Cancellation on Seller Unverify (Admin Action) ---")
    # Reset seller and order
    seller_profile.is_verified = True
    seller_profile.save()
    order.status = 'pending'
    order.admin_notes = ''
    order.save()
    
    # Login as admin to get token
    _, admin_login_json = make_request('POST', '/api/v1/auth/login/', data={'email': 'admin@abc.com', 'password': 'password123'})
    admin_token = admin_login_json['tokens']['access']
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    status_code, response_json = make_request('PATCH', f'/api/v1/admin/sellers/{seller_profile.id}/verify/', data={'action': 'unverify'}, headers=headers)
    print(f"Status: {status_code}")
    print(f"Response: {response_json}")
    
    order.refresh_from_db()
    print(f"Order Status after unverify: {order.status}")
    print(f"Order Admin Notes: {order.admin_notes}")
    assert order.status == 'cancelled'
    assert 'refund amount will be transferred' in order.admin_notes
    print("Test 3 PASS")
    
    print("\n--- Test 4: Refund Notes in API Response ---")
    buyer.is_active = True
    buyer.save()
    
    # Login as buyer to get token
    _, buyer_login_json = make_request('POST', '/api/v1/auth/login/', data={'email': 'test_buyer@abc.com', 'password': 'password123'})
    buyer_token = buyer_login_json['tokens']['access']
    buyer_headers = {'Authorization': f'Bearer {buyer_token}'}
    
    status_code, response_json = make_request('GET', f'/api/v1/orders/{order.order_number}/', headers=buyer_headers)
    print(f"Status: {status_code}")
    print(f"Admin Notes returned: {response_json.get('admin_notes')}")
    assert 'admin_notes' in response_json
    assert 'refund amount will be transferred' in response_json['admin_notes']
    print("Test 4 PASS")
    
    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
