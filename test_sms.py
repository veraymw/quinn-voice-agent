#!/usr/bin/env python3
"""
Test script for SMS booking functionality
"""
import httpx
import json
import asyncio
from datetime import datetime

async def test_sms_booking(phone_number: str, first_name: str = "Test", company: str = "Test Company"):
    """Test the SMS booking endpoint"""
    
    # SMS booking payload
    payload = {
        "call_control_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "phone_number": phone_number,
        "first_name": first_name,
        "last_name": "User",
        "company": company,
        "region": "Americas",
        "qualification_level": "SQL",
        "qualification_score": 85
    }
    
    print(f"🚀 Testing SMS to {phone_number}")
    print(f"📱 Message will be sent from Quinn Voice Agent")
    print(f"🔗 Will include personalized booking link")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "http://localhost:8000/tools/send-booking-sms",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("✅ SMS sent successfully!")
                    print(f"📊 Response: {json.dumps(result, indent=2)}")
                else:
                    print("❌ SMS failed:")
                    print(f"🔍 Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"🔍 Response: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Could not connect to server")
        print("💡 Make sure the FastAPI server is running:")
        print("   uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Test with your actual phone number
    phone_number = "+19296027097"  # Your phone number
    
    print("=" * 50)
    print("📱 Quinn Voice Agent - SMS Test")
    print("=" * 50)
    print(f"🎯 Testing SMS to: {phone_number}")
    print("📞 Simulating a qualified SQL lead call scenario")
    print()
    
    asyncio.run(test_sms_booking(
        phone_number=phone_number,
        first_name="Vera",
        company="Your Company"
    ))
