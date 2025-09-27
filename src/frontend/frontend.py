"""Fake frontend for testing purposes"""

import requests

BASE_URL = "http://localhost:5020/agent"


def log_in():
    print("Welcome! Please log in.")
    name = input("Enter your name: ").strip()
    email = input("Enter your email: ").strip()

    payload = {"name": name, "email": email}
    response = requests.post(f"{BASE_URL}/log_in", json=payload)
    response.raise_for_status()

    data = response.json()
    if data.get("new_user"):
        print(f"✅ Welcome, {data['name']}! We're now redirecting you to one of our agents...")
    else:
        print(f"👋 Welcome back, {data['name']}! We're now redirecting you to one of our agents...")

    return data["id"]


def start_conversation(customer_id: str) -> str:
    payload = {"customer_id": customer_id}
    response = requests.post(f"{BASE_URL}/start_conversation", json=payload)
    response.raise_for_status()
    data = response.json()
    print(f"\n🤖 Agent: {data['message']}")
    return data["conversation_id"]


def chat_loop(conversation_id: str):
    while True:
        user_msg = input("You: ").strip()
        if not user_msg or user_msg.lower() in {"quit", "exit"}:
            print("👋 Ending conversation. Goodbye!")
            break

        payload = {"message": user_msg}
        response = requests.post(f"{BASE_URL}/chat/{conversation_id}", json=payload)
        response.raise_for_status()
        data = response.json()

        print(f"🤖 Agent: {data['reply']}")
        if not data.get("missing_fields"):
            print("✅ All required information collected.")
            break


if __name__ == "__main__":
    print("=== Fake Frontend ===")
    customer_id = log_in()
    conversation_id = start_conversation(customer_id)
    chat_loop(conversation_id)
