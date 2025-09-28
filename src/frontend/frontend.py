"""Fake frontend for testing purposes"""

from logging import getLogger
from typing import cast

import requests
from typing_extensions import Literal

from conversational_agent.data_models.db_models import IssueStatus

logger = getLogger(__name__)

BASE_URL = "http://localhost:5020/agent"


def log_in():
    print("Welcome! Please log in.")
    name = input("Enter your name: ").strip()
    import re

    email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    while True:
        email = input("Enter your email: ").strip()
        if re.match(email_pattern, email):
            break
        print("❌ Invalid email format. Please try again.")

    payload = {"name": name, "email": email}
    response = requests.post(f"{BASE_URL}/log_in", json=payload)
    response.raise_for_status()

    data = response.json()
    if data.get("new_user"):
        print(f"✅ Welcome, {data['name']}!")
    else:
        print(f"👋 Welcome back, {data['name']}!")

    return data["id"]


def get_choice() -> Literal["summary", "new"]:
    """Get user choice to either get a conversation summary or start a new conversation."""
    while True:
        choice = (
            input(
                "Type 'summary' to get a conversation summary or 'new' to start a new conversation: "
            )
            .strip()
            .lower()
        )
        if choice in {"summary", "new"}:
            return cast(Literal["summary", "new"], choice)
        print("❌ Invalid choice. Please type 'summary' or 'new'.")


def start_conversation(customer_id: str) -> str:
    payload = {"customer_id": customer_id}
    response = requests.post(f"{BASE_URL}/start_conversation", json=payload)
    response.raise_for_status()
    data = response.json()
    print("✅ Directing you to one of our agents...")
    print(f"\n🤖 Agent: {data['message'].encode('utf-8').decode('unicode_escape')}")
    return data["conversation_id"]


def get_conversation_summary():
    while True:
        conversation_id = input("Enter the conversation ID to summarize: ").strip()
        try:
            response = requests.get(f"{BASE_URL}/{conversation_id}/summary")
            response.raise_for_status()
            data = response.json()
            print(f"\n📝 Conversation Summary: {data}")
            break
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, "status_code"):
                if e.response.status_code == 404:
                    print("❌ Conversation ID not found. Please try another ID.")
                    continue
                if e.response.status_code == 422:
                    print("❌ Invalid UUID format. Please enter a valid conversation ID.")
                    continue

            print(f"❌ Error: {e}")
            break


def chat_loop(conversation_id: str):
    while True:
        user_msg = input("😁 You: ").strip()
        if not user_msg or user_msg.lower() in {"quit", "exit"}:
            print("👋 Ending conversation. Goodbye!")
            break

        payload = {"message": user_msg}
        response = requests.post(f"{BASE_URL}/chat/{conversation_id}", json=payload)
        response.raise_for_status()
        data = response.json()

        print(f"🤖 Agent: {data['reply']}")
        match data.get("status"):
            case IssueStatus.RESOLVED:
                print("✅ Your issue has been marked as resolved. Ending conversation.")
                break
            case IssueStatus.CLOSED:
                print("✅ Your issue has been marked as closed. Ending conversation.")
                break
            case IssueStatus.REQUIRES_MANUAL_REVIEW:
                print(
                    "⚠️ Your issue requires manual review by a human agent. "
                    "You will be contacted on your registered email shortly. Ending conversation."
                )
                break
            case _:
                logger.info(f"ℹ️ Current issue status: {data.get('status')}")


if __name__ == "__main__":
    print("=== Fake Frontend ===")
    customer_id = log_in()
    choice = get_choice()
    if choice == "summary":
        get_conversation_summary()
    else:
        conversation_id = start_conversation(customer_id)
        chat_loop(conversation_id)
