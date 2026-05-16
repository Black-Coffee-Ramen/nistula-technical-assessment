import asyncio
import time
from collections import Counter
import json

import httpx

BASE_URL = "http://localhost:8000"

TEST_PAYLOADS = [

    # =========================================================
    # FACTUAL / OPERATIONAL QUERIES
    # =========================================================

    {
        "name": "WiFi Password Query",
        "payload": {
            "source": "airbnb",
            "guest_name": "John Doe",
            "message": "What is the WiFi password?",
            "timestamp": "2026-05-07T09:00:00Z",
            "booking_ref": "NIS-2024-0915",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Check-In Time Query",
        "payload": {
            "source": "instagram",
            "guest_name": "Emma Wilson",
            "message": "What time is check-in?",
            "timestamp": "2026-05-07T11:00:00Z",
            "booking_ref": "NIS-2024-0916",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Cancellation Policy Query",
        "payload": {
            "source": "direct",
            "guest_name": "Michael Lee",
            "message": "What is your cancellation policy?",
            "timestamp": "2026-05-07T12:00:00Z",
            "booking_ref": "NIS-2024-0917",
            "property_id": "villa-b1"
        }
    },

    # =========================================================
    # PRICING + AVAILABILITY
    # =========================================================

    {
        "name": "Pricing + Availability Query",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Rahul Sharma",
            "message": (
                "Is the villa available from April 20 to 24? "
                "What is the rate for 2 adults?"
            ),
            "timestamp": "2026-05-05T10:30:00Z",
            "booking_ref": "NIS-2024-0891",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Extra Guest Pricing",
        "payload": {
            "source": "booking_com",
            "guest_name": "Sarah Kim",
            "message": "How much do you charge for extra guests?",
            "timestamp": "2026-05-08T10:30:00Z",
            "booking_ref": "NIS-2024-0918",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Long Stay Pricing",
        "payload": {
            "source": "airbnb",
            "guest_name": "David Brown",
            "message": "Do you offer discounts for monthly stays?",
            "timestamp": "2026-05-08T11:00:00Z",
            "booking_ref": "NIS-2024-0919",
            "property_id": "villa-b1"
        }
    },

    # =========================================================
    # SPECIAL REQUESTS
    # =========================================================

    {
        "name": "Airport Pickup Request",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Sophia Patel",
            "message": "Can you arrange airport pickup for us?",
            "timestamp": "2026-05-08T12:00:00Z",
            "booking_ref": "NIS-2024-0920",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Early Check-In Request",
        "payload": {
            "source": "instagram",
            "guest_name": "Chris Martin",
            "message": "Can we check in early around 10am?",
            "timestamp": "2026-05-08T13:00:00Z",
            "booking_ref": "NIS-2024-0921",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Birthday Decoration Request",
        "payload": {
            "source": "direct",
            "guest_name": "Priya Nair",
            "message": "Can you arrange birthday decorations at the villa?",
            "timestamp": "2026-05-08T14:00:00Z",
            "booking_ref": "NIS-2024-0922",
            "property_id": "villa-b1"
        }
    },

    # =========================================================
    # COMPLAINTS
    # =========================================================

    {
        "name": "AC Complaint",
        "payload": {
            "source": "booking_com",
            "guest_name": "Anjali Gupta",
            "message": "The AC is not cooling properly and the room is very hot.",
            "timestamp": "2026-05-06T14:15:00Z",
            "booking_ref": "NIS-2024-0902",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Hot Water Complaint",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Kevin Roy",
            "message": "There is no hot water in the bathroom.",
            "timestamp": "2026-05-09T08:00:00Z",
            "booking_ref": "NIS-2024-0923",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Refund Demand Complaint",
        "payload": {
            "source": "airbnb",
            "guest_name": "Jessica Moore",
            "message": "This experience has been terrible. I want a refund immediately.",
            "timestamp": "2026-05-09T09:00:00Z",
            "booking_ref": "NIS-2024-0924",
            "property_id": "villa-b1"
        }
    },

    # =========================================================
    # MIXED / AMBIGUOUS QUERIES
    # =========================================================

    {
        "name": "WiFi + Early Check-In",
        "payload": {
            "source": "instagram",
            "guest_name": "Noah Walker",
            "message": "Can we check in early and what is the WiFi password?",
            "timestamp": "2026-05-09T10:00:00Z",
            "booking_ref": "NIS-2024-0925",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Rate + Airport Pickup",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Olivia Taylor",
            "message": "What is the rate and can you arrange airport pickup?",
            "timestamp": "2026-05-09T11:00:00Z",
            "booking_ref": "NIS-2024-0926",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "WiFi Slow + Late Checkout",
        "payload": {
            "source": "booking_com",
            "guest_name": "Lucas Hall",
            "message": "The WiFi is slow and we may need late checkout tomorrow.",
            "timestamp": "2026-05-09T12:00:00Z",
            "booking_ref": "NIS-2024-0927",
            "property_id": "villa-b1"
        }
    },

    # =========================================================
    # HUMAN-LIKE EDGE CASES
    # =========================================================

    {
        "name": "Typo Message",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Test User",
            "message": "whts da wifi pass?",
            "timestamp": "2026-05-10T10:00:00Z",
            "booking_ref": "NIS-2024-0928",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Emoji Heavy Query",
        "payload": {
            "source": "instagram",
            "guest_name": "Emoji User",
            "message": "Pool looks amazing 😍😍😍 can we bring pets? 🐶",
            "timestamp": "2026-05-10T11:00:00Z",
            "booking_ref": "NIS-2024-0929",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Very Short Message",
        "payload": {
            "source": "direct",
            "guest_name": "Short Msg",
            "message": "available?",
            "timestamp": "2026-05-10T12:00:00Z",
            "booking_ref": "NIS-2024-0930",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Mixed Casing",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Mixed Case",
            "message": "CAN WE CHECK IN EARLY",
            "timestamp": "2026-05-10T13:00:00Z",
            "booking_ref": "NIS-2024-0931",
            "property_id": "villa-b1"
        }
    },

    # =========================================================
    # INVALID PAYLOADS
    # =========================================================

    {
        "name": "Invalid Property",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Invalid Property User",
            "message": "Hello",
            "timestamp": "2026-05-10T14:00:00Z",
            "booking_ref": "NIS-2024-0932",
            "property_id": "villa-x9"
        }
    },

    {
        "name": "Missing Property ID",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Missing Field",
            "message": "Need assistance",
            "timestamp": "2026-05-10T15:00:00Z",
            "booking_ref": "NIS-2024-0933"
        }
    },

    {
        "name": "Invalid Timestamp",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Bad Timestamp",
            "message": "Help",
            "timestamp": "yesterday-night",
            "booking_ref": "NIS-2024-0934",
            "property_id": "villa-b1"
        }
    },

    {
        "name": "Empty Message",
        "payload": {
            "source": "whatsapp",
            "guest_name": "Empty Message User",
            "message": "",
            "timestamp": "2026-05-10T16:00:00Z",
            "booking_ref": "NIS-2024-0935",
            "property_id": "villa-b1"
        }
    }
]

# =========================================================
# METRICS + ANALYTICS
# =========================================================

stats = {
    "total": 0,
    "claude_failures": Counter(),
    "fallback_activations": Counter({
        "deterministic_safe": 0,
        "suppressed_unsafe": 0
    }),
    "actions": Counter()
}


# =========================================================
# TEST RUNNER
# =========================================================

async def run_tests():
    async with httpx.AsyncClient(timeout=20.0) as client:

        for test in TEST_PAYLOADS:
            stats["total"] += 1

            print("\n" + "=" * 80)
            print(f"TEST: {test['name']}")
            print("=" * 80)
            print(f"REQUEST PAYLOAD:")
            print(json.dumps(test["payload"], indent=2))
            print("-" * 80)

            start = time.perf_counter()

            try:
                response = await client.post(
                    f"{BASE_URL}/webhook/message",
                    json=test["payload"]
                )

                duration = (time.perf_counter() - start) * 1000

                print(f"STATUS: {response.status_code} | TIME: {duration:.2f} ms")
                print("-" * 80)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"RESPONSE JSON:")
                    print(json.dumps(data, indent=2))
                    
                    action = data.get("action")
                    reply = data.get("drafted_reply", "")
                    stats["actions"][action] += 1

                    # Patch 6: Validation for Pricing/Availability Fallbacks
                    if "Villa B1 is available for April 20–24" in reply:
                        stats["fallback_activations"]["deterministic_safe"] += 1
                        print("\n✓ Availability fallback verified via content.")
                    
                    if "base rate is INR 18,000" in reply:
                        stats["fallback_activations"]["deterministic_safe"] += 1
                        print("\n✓ Pricing fallback verified via content.")

                    # Complaint escalation verification
                    if "Complaint" in test["name"] and action != "escalate":
                        print(f"\n⚠ WARNING: Complaint '{test['name']}' did not escalate properly!")

                else:
                    print(f"ERROR RESPONSE:")
                    print(f"Status: {response.status_code}")
                    print(f"Body: {response.text}")

            except Exception as e:
                print(f"EXCEPTION: {e}")
            
            print("=" * 80)


# =========================================================
# CONCURRENCY TEST
# =========================================================

async def concurrency_test():

    print("\n" + "=" * 80)
    print("CONCURRENCY TEST (10 PARALLEL REQUESTS)")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=20.0) as client:

        async def send_request(index: int):

            payload = {
                "source": "whatsapp",
                "guest_name": f"Concurrent User {index}",
                "message": (
                    f"Is villa available for request {index}?"
                ),
                "timestamp": "2026-05-11T10:00:00Z",
                "booking_ref": f"NIS-CON-{index}",
                "property_id": "villa-b1"
            }

            print(f"\n--- CONCURRENT REQUEST {index} ---")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = await client.post(
                f"{BASE_URL}/webhook/message",
                json=payload
            )

            print(f"Request {index} | Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response {index}:")
                print(json.dumps(data, indent=2))
                stats["actions"][data.get("action")] += 1
            else:
                print(f"Error Response {index}: {response.text}")
            
            print("-" * 40)

        await asyncio.gather(
            *[send_request(i) for i in range(10)]
        )


# =========================================================
# SUMMARY REPORT
# =========================================================

def print_summary():

    print("\n" + "=" * 80)
    print("FINAL OPERATIONAL SUMMARY")
    print("=" * 80)

    print(
        f"Total Requests Processed: "
        f"{stats['total'] + 10}"
    )

    print("\nAction Distribution:")

    for action, count in stats["actions"].items():
        print(f"- {action}: {count}")

    print("\nNote:")
    print(
        "For detailed decision rationale and internal "
        "correlation IDs, check the application logs (app.log)."
    )

    print("=" * 80 + "\n")


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    print("\n🚀 NISTULA BACKEND TEST SUITE")
    print("📡 Showing full JSON responses for all requests\n")

    asyncio.run(run_tests())
    asyncio.run(concurrency_test())

    print_summary()