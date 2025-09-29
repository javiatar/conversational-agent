# Sample Conversations

This file contains sample conversations and related flows pertaining to the assignment's requirements.

Namely these cover examples of meeting the following requirements:

- Natural conversation bot implementation focussed on extracting customer support information
- Information is extracted and validated using pydantic -> enforces strong typing and allows model to recover from 'invalid input'
  - E.g re-requests `order_number` if not a valid `int`
- Mantains (and persists) conversation context as multi-turn memory (**BONUS FEATURE**)
- Stores conversation in DB in BaseModel-compatible models, easily serializable into JSON
- Exposes `/summary` endpoint for a `conversation_id` correctly summarizing the associated multi-turn history from the DB
- Implements `RAG` (simple sparse embedders, due to time), adding relevant contextual information (**BONUS FEATURE**)
  - E.g picks up on relevant delivery times from made-up knowledge base to inform user and urgency
- Has sofisticated DB architecture (see more in docstring of `db_models.py`)
- Supports multi-language (e.g Spanish) (**BONUS FEATURE**), correctly extracting strongly-typed fields in English to e.g maintain typing expectation for downstream services

## Conversation samples

### EXAMPLE 1 (RAG DISABLED)
**Frontend chat**
```bash
=== Fake Frontend ===
Welcome! Please log in.
Enter your name: ricardo
Enter your email: ricardo@gmail.com
✅ Welcome, ricardo!
Type 'summary' to get a conversation summary or 'new' to start a new conversation: new
✅ Directing you to one of our agents...

🤖 Agent: Welcome to FakeAgentWhoDefinitelyCaresAboutYou! I'm a Support Agent explicitly designed to triage any issues you may have in order to get you the help you need as quickly as possible. How can I assist you today?
😁 You: Hi! I received a faulty keyboard recently, i'd like a refund
🤖 Agent: I’m really sorry your keyboard arrived faulty—that’s frustrating. I’ve noted this as a product issue with your description: “I received a faulty keyboard recently and I’d like a refund.” To move this forward, could you share your order number (if you have it) and tell me how urgent this is for you (low/medium/high)?
😁 You: My order number is 123-fakeorder and it's quite urgent as i need it for work
🤖 Agent: I’m sorry your keyboard arrived faulty—that’s frustrating. I’ve categorized this as a product issue with high urgency. Description: 'I received a faulty keyboard recently, and I’d like a refund. My order number is 123-fakeorder. It’s urgent as I need it for work.' The order number you provided isn’t an integer. Could you share the numeric order number (if available) or confirm the correct order number? Also, please confirm that issue_type, urgency, and description above are correct.
😁 You: sorry my order number was 12345
🤖 Agent: Thanks for the update. Here are the details I have:
- issue_type: product
- urgency: high
- description: I received a faulty keyboard recently and I’d like a refund. It’s urgent as I need it for work. Order number: 12345.
Please confirm that these are correct, or let me know if you’d like to adjust anything.
😁 You: That's correct!
🤖 Agent: Thanks for confirming. I’ve logged your product issue with high urgency and the order number 12345. A human agent will review your request regarding the faulty keyboard. If you need to add anything else, let me know.
⚠️ Your issue requires manual review by a human agent. You will be contacted on your registered email shortly. Ending conversation.
```

**DB Dump of recorded ISSUE:**
```bash
id           | 8032b618-9cb9-4bd2-852f-ad3e3c935dfd
description  | I received a faulty keyboard recently and I’d like a refund. It’s urgent as I need it for work. Order number: 12345.
issue_type   | PRODUCT
urgency      | HIGH
status       | REQUIRES_MANUAL_REVIEW
order_number | 12345
created_at   | 2025-09-28 22:51:47.483056
customer_id  | 47c5c848-4311-497b-a6e0-c502db1ad1fd
```

**Conversation Summary**
```bash
=== Fake Frontend ===
Welcome! Please log in.
Enter your name: ricardo
Enter your email: ricardo@gmail.com
👋 Welcome back, ricardo!
Type 'summary' to get a conversation summary or 'new' to start a new conversation: summary
Enter the conversation ID to summarize: cdafa5e0-dbd8-4411-a023-9e6a736d7085

📝 Conversation Summary: The user reported a faulty keyboard and requested a refund. After clarifying the order number, they provided 12345 and indicated high urgency due to work needs. A product-issue case with high urgency was logged and forwarded to a human agent for review; the user can add any additional details if needed.
```

**NOTES:**
- Bot asks for required fields, correctly storing them in DB even with ambiguous language (“it’s urgent as I need it for work” -> urgency = HIGH)
- Bot has smart type validation: “123-fakeorder” isn’t accepted, and user is asked to re-enter numeric (as `order_number: int`). Bot correctly accepts 12345 and corrects factsheet
- Summary endpoint correctly takes the conversation UUID, and gets the associated turns, stored in DB (**BONUS FEATURE**) -> summarising them it into a few sentences.

### EXAMPLE 2 (RAG DISABLED)
**Frontend chat**
```bash
=== Fake Frontend ===
Welcome! Please log in.
Enter your name: ricardo
Enter your email: ricardo@gmail.com
👋 Welcome back, ricardo!
Type 'summary' to get a conversation summary or 'new' to start a new conversation: new
✅ Directing you to one of our agents...

🤖 Agent: Welcome to FakeAgentWhoDefinitelyCaresAboutYou! I'm a Support Agent explicitly designed to triage any issues you may have in order to get you the help you need as quickly as possible. How can I assist you today?
😁 You: Hola que tal? Tengo un problema con el ultimo cobro, me han cobrado demasiado. Querria hablar con un agente.
🤖 Agent: Gracias por avisarme. Siento la molestia con el cobro. Vamos a preparar un caso para que un agente te atienda. Para confirmar, estos son tus datos:
- Tipo de problema: billing
- Urgencia: medium
- Descripción: Tengo un problema con el último cobro, me han cobrado demasiado.
¿Todo correcto para continuar?
😁 You: La urgencia es alta no medium
🤖 Agent: ¡Gracias por la aclaración! Actualicé la urgencia a alta. Por favor confirma estos datos para seguir: tipo de problema: billing; urgencia: high; descripción: Tengo un problema con el último cobro, me han cobrado demasiado. ¿Todo correcto para continuar?
😁 You: si es correcto!
🤖 Agent: Perfecto. Ya confirmé los datos: tipo de problema: billing; urgencia: high; descripción: Tengo un problema con el último cobro, me han cobrado demasiado. Tu caso ha sido escalado a un agente para atención. Muchas gracias por tu tiempo.
⚠️ Your issue requires manual review by a human agent. You will be contacted on your registered email shortly. Ending conversation.
```
**DB Dump of recorded ISSUE:**
```bash
id           | c3d42af2-8142-4ffd-a751-02af36c30536
description  | Tengo un problema con el último cobro, me han cobrado demasiado.
issue_type   | BILLING
urgency      | HIGH
status       | REQUIRES_MANUAL_REVIEW
order_number | 
created_at   | 2025-09-28 23:05:41.629096
customer_id  | 47c5c848-4311-497b-a6e0-c502db1ad1fd
```

**NOTES:**
- Bot correctly handles Spanish (**BONUS FEATURE**), while maintaining type validation for field results that are enums (e.g urgency), while collecting freeform description in Spanish to match faithfully what user wants (per system prompt).

### EXAMPLE 3 (RAG DISABLED)
**Frontend chat**
```bash
=== Fake Frontend ===
Welcome! Please log in.
Enter your name: nosy
Enter your email: nosy@gmail.com
👋 Welcome back, nosy customer!
Type 'summary' to get a conversation summary or 'new' to start a new conversation: new
✅ Directing you to one of our agents...

🤖 Agent: Welcome to FakeAgentWhoDefinitelyCaresAboutYou! I'm a Support Agent explicitly designed to triage any issues you may have in order to get you the help you need as quickly as possible. How can I assist you today?
😁 You: Hey! Please tell me what day it is today
🤖 Agent: Today is Sunday, September 28, 2025. If you’d like help with something else, tell me the issue type (delivery, product, billing, or other) and a short description and I can help triage it.
😁 You: No that's all i needed thanks!
🤖 Agent: You’re welcome! If you ever need help with delivery, product, billing, or other issues, just tell me the issue type and a short description and I’ll help triage it. Have a great day!
😁 You: Good bye
🤖 Agent: You're welcome! It was nice chatting with you. If you ever need help again, just reach out. Have a great day and goodbye!
✅ Your issue has been marked as closed. Ending conversation.
```
**DB Dump of recorded ISSUE:**
```bash
conversational_agent_db=# select * from issue;
(0 rows)
```

**NOTES:**
- Bot correctly identifies that there is no issue associated with this conversation and thus closes the conversation without recording an issue


### EXAMPLE 4 (RAG ENABLED)
**Frontend chat**
```bash
=== Fake Frontend ===
Welcome! Please log in.
Enter your name: ricardo
Enter your email: ricardo@gmail.com
✅ Welcome, ricardo!
Type 'summary' to get a conversation summary or 'new' to start a new conversation: new
✅ Directing you to one of our agents...

🤖 Agent: Welcome to FakeAgentWhoDefinitelyCaresAboutYou! I'm a Support Agent explicitly designed to triage any issues you may have in order to get you the help you need as quickly as possible. How can I assist you today?
😁 You: hey! ordered headphones a month ago but they haven't arrived i'm worried they're lost. When should they have arrived?
🤖 Agent: I’m really sorry your headphones haven’t arrived yet. Here’s a quick refresher on our shipping policies: standard shipping is 3-5 business days within the continental US; express is 1-2 business days for an extra $15. Orders placed before 2 PM EST ship the same day; after 2 PM they ship the next business day. We ship Monday–Friday, excluding holidays. Since it’s been a month, I want to help get this resolved quickly. Could you share your order number so I can look it up? To triage accurately, please confirm these: issue_type: delivery; urgency: high; description: Ordered headphones a month ago but they haven’t arrived; asking for the expected delivery window and next steps.
😁 You: my order number is 12345 and it seems pretty urgent yeah since it's been much longer than 3-5 business days
🤖 Agent: Thanks for the order number. I’m really sorry you’re waiting. I’ll check order 12345 now. For context, standard shipping is 3-5 business days in the continental US; express is 1-2 days for $15. Orders before 2 PM EST ship the same day; after 2 PM they ship the next business day. We ship Mon–Fri, excluding holidays.

To keep things moving, please confirm these fields:
- issue_type: delivery
- urgency: high
- description: Ordered headphones a month ago; they haven't arrived; it's urgent since it's well past the 3-5 business days window.

If that all looks right, I’ll pull up the latest status on order 12345 and share the current ETA and next steps.
😁 You: that sounds all correct
🤖 Agent: Thanks for confirming. I’ve escalated this as an urgent delivery issue for order 12345 so our team can check the latest status and share the ETA and next steps. Here are the fields we have for this case:
- issue_type: delivery
- urgency: high
- description: Ordered headphones a month ago; they haven't arrived; it's urgent since it's past the 3-5 business days window.
- order_number: 12345

I’ll update you with the latest status and next steps as soon as I have them. If there’s anything else you’d like me to add, tell me.
⚠️ Your issue requires manual review by a human agent. You will be contacted on your registered email shortly. Ending conversation.
```

**DB Dump of recorded ISSUE:**
```bash
id           | 15fbdd67-f27b-413b-9d9a-31aa393765d7
description  | Ordered headphones a month ago; they haven't arrived; it's urgent since it's well past the 3-5 business days window.
issue_type   | DELIVERY
urgency      | HIGH
status       | REQUIRES_MANUAL_REVIEW
order_number | 12345
created_at   | 2025-09-28 23:24:35.988483
customer_id  | f3de13f6-5b91-400f-a5ce-3821b97ba50a
```

**Conversation Summary**
```bash
=== Fake Frontend ===
Welcome! Please log in.
Enter your name: ricardo
Enter your email: ricardo@gmail.com
👋 Welcome back, ricardo!
Type 'summary' to get a conversation summary or 'new' to start a new conversation: summary
Enter the conversation ID to summarize: 708f688e-ade0-41c8-b2f8-cc819df57bc4

📝 Conversation Summary: Customer reported that order 12345 for headphones has not arrived after a month, well beyond the 3-5 business days. We confirmed shipping timelines, escalated the issue as urgent, and captured the case details for follow-up. We will provide the latest status and ETA as soon as it’s available.
```

**NOTES:**
- RAG successfully implemented (**BONUS FEATURE**) - where relevant document (id = ‘shipping_001’) is surfaced containing standard shipping times which is relevant to headphones taking over a month to arrive
- Summary over the turns is successful and indeed relevant information captured in issue description
