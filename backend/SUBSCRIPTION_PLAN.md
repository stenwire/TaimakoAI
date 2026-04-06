To set up a subscription API for your FastAPI project using Paystack, you should follow a "Transaction-First" flow. This is the most reliable way to handle the initial payment and automatic subscription.

### 1. High-Level Flow
1.  **Selection:** User selects a plan (`nexus` or `flux`).
2.  **Initialization:** Your API calls Paystack's **Initialize Transaction** endpoint with the specific `plan_code`.
3.  **Payment:** The user is redirected to Paystack to pay. Upon successful payment, Paystack automatically creates a **Subscription** and a **Customer**.
4.  **Notification:** Paystack sends a `subscription.create` and `charge.success` event to your **Webhook**.
5.  **Provisioning:** Your webhook updates your database to grant the user access based on the plan.

---

### 2. Implementation Steps

#### Step 1: Configuration & Plan Mapping
Store your Paystack secret key and map your internal plan names to the Paystack `plan_code` you created in your dashboard.

```python
# .env
PAYSTACK_SECRET_KEY=sk_test_xxxxxx
PAYSTACK_WEBHOOK_SECRET=xxxxxx  # For signature verification

# config.py
PLAN_MAPPING = {
    "nexus": "PLN_nexus_code_here",
    "flux": "PLN_flux_code_here"
}
```

#### Step 2: Database Models
You need to track the subscription status and the Paystack unique identifiers.

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    paystack_customer_code = Column(String, nullable=True)
    subscription_code = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive") # active, non-renewing, attention, cancelled
    plan_type = Column(String, nullable=True) # nexus, flux
```

#### Step 3: Paystack Service (FastAPI Utility)
Use `httpx` for asynchronous requests to Paystack.

```python
import httpx
from .config import PAYSTACK_SECRET_KEY

async def initialize_subscription(email: str, plan_code: str):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    payload = {
        "email": email,
        "plan": plan_code,
        "callback_url": "https://yourfrontend.com/payment-verify" 
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
```

#### Step 4: The Initialization Endpoint
This is what the user clicks to start their subscription.

```python
@app.post("/subscribe/{plan_name}")
async def start_subscription(plan_name: str, current_user: User = Depends(get_current_user)):
    if plan_name not in PLAN_MAPPING:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan_code = PLAN_MAPPING[plan_name]
    res = await initialize_subscription(current_user.email, plan_code)
    
    if res["status"]:
        # Return the authorization_url to the frontend to redirect the user
        return {"checkout_url": res["data"]["authorization_url"]}
    raise HTTPException(status_code=400, detail="Could not initialize payment")
```

#### Step 5: Webhook Handler (Crucial for Security)
Paystack will notify your backend when payments occur or subscriptions are created. **You must verify the signature.**

```python
import hmac
import hashlib

@app.post("/paystack/webhook")
async def paystack_webhook(request: Request, x_paystack_signature: str = Header(None)):
    # 1. Verify Signature
    body = await request.body()
    computed_signature = hmac.new(
        PAYSTACK_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if computed_signature != x_paystack_signature:
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event = payload["event"]
    data = payload["data"]

    # 2. Handle Events
    if event == "subscription.create":
        # Store the subscription_code and customer_code in DB
        user_email = data["customer"]["email"]
        # Update user record: set subscription_code, status='active'
        
    elif event == "charge.success":
        # Initial or recurring payment succeeded
        # Ensure user access is extended
        
    elif event == "subscription.disable" or event == "invoice.payment_failed":
        # Revoke access or notify user
        pass

    return {"status": "success"}
```

#### Step 6: Subscription Management (Cancellation)
To cancel, you need the `subscription_code` and `email_token` (returned by Paystack during the `subscription.create` event).

```python
async def cancel_subscription(subscription_code: str, email_token: str):
    url = "https://api.paystack.co/subscription/disable"
    payload = {"code": subscription_code, "token": email_token}
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.status_code == 200
```

#### Step 7: Subscription Management (Renewal)


### 3. Key Tips for Your Setup
*   **Don't rely on the frontend callback:** The user might close their browser before the callback triggers. Always rely on the **Webhook** to update the subscription status in your database.
*   **Customer Creation:** You don't need to manually create a customer first. Calling the `initialize` endpoint with an email automatically creates or retrieves the customer on Paystack's end.
*   **Metadata:** You can pass `metadata: {"user_id": 123}` in the initialization request. This metadata will be sent back in the webhook payload, making it easier to link the payment to your local user ID.
*   **Testing:** Use Paystack's test cards (e.g., the "Success" card) to trigger the `subscription.create` webhook locally using a tool like **ngrok** to expose your FastAPI server.


Subscription Renewal & Upgrade Implementation

Since Paystack handles renewals automatically, your primary job is to listen for success/failure events and provide a flow for users to switch between your nexus and flux plans.

1. Handling Automatic Renewals

Paystack manages the billing cycle for you.[1][2] You only need to respond to the webhooks to keep your database in sync.

Webhook Logic for Renewals

When a renewal occurs, Paystack sends a charge.success event.[1][2][3] The payload will contain the plan code and the subscription_code.

code
Python
download
content_copy
expand_less
# Inside your webhook handler
if event == "charge.success":
    data = payload["data"]
    # Check if this charge belongs to a subscription
    subscription_code = data.get("plan", {}).get("subscription_code")
    
    if subscription_code:
        # This is a renewal payment
        user = db.query(User).filter(User.subscription_code == subscription_code).first()
        if user:
            user.subscription_status = "active"
            user.last_payment_date = datetime.utcnow()
            db.commit()

elif event == "invoice.payment_failed":
    # Renewal failed (e.g., insufficient funds)
    subscription_code = data["subscription"]["subscription_code"]
    user = db.query(User).filter(User.subscription_code == subscription_code).first()
    if user:
        user.subscription_status = "attention" # User has access but needs to pay
        db.commit()
2. Plan Upgrades (e.g., Nexus → Flux)

Paystack does not have a "Change Plan" button for an existing subscription ID.[3] To upgrade a user, you must disable the old subscription and create a new one.

Strategy A: Immediate Upgrade (Charge Now)

Use this if you want the user to pay the full price of the new plan immediately.

Initialize Transaction: Call the initialize endpoint with the new plan_code.[1][3]

Verify & Cleanup: Once the user pays, disable the old nexus subscription and store the new flux subscription code.

Strategy B: Seamless Upgrade (Use Existing Card)

If you already have the user's authorization_code (from their first payment), you can create the new subscription via API without the user typing their card details again.

code
Python
download
content_copy
expand_less
async def upgrade_user_plan(user: User, new_plan_name: str):
    # 1. Get the new plan code
    new_plan_code = PLAN_MAPPING[new_plan_name]
    
    # 2. Disable current subscription first
    # (Optional: You can wait for the new one to succeed first)
    await cancel_subscription(user.subscription_code, user.email_token)

    # 3. Create new subscription using saved authorization
    url = "https://api.paystack.co/subscription"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    payload = {
        "customer": user.paystack_customer_code,
        "plan": new_plan_code,
        "authorization": user.last_authorization_code # Stored during first payment
    }
    
    async with httpx.AsyncClient() as client:
        res = await client.post(url, json=payload, headers=headers)
        data = res.json()
        if data["status"]:
            user.subscription_code = data["data"]["subscription_code"]
            user.plan_type = new_plan_name
            # Paystack will charge the card immediately for the new plan
            return {"message": "Upgraded successfully"}
3. Plan Downgrades

Downgrades are usually handled at the end of the current billing cycle to avoid "loosing" money the user already paid.

Request received: User clicks "Downgrade to Nexus".[3]

Set to Cancel: Call the Paystack Disable Subscription endpoint, but only at the end of the period or use the "non-renewing" status logic.

New Subscription: On the day the old plan expires, your system (via a background task or the subscription.disable webhook) creates the new lower-tier subscription.

4. Important Considerations

Proration: Paystack does not support native proration (e.g., charging only the $5 difference for half a month). Most developers either:

Charge Full Price: Start the new plan immediately (simplest).

Delay Upgrade: Wait until the current month ends, then switch.

Retry Logic: Paystack does not retry failed subscription renewals.[1][2][3] If a renewal fails, the status becomes attention.[6] You should email the user with a payment link to reactivate.[1][7]

Authorization Storage: Always save the authorization_code from the first successful charge.success event. You need this code to perform manual charges or programmatically create new subscriptions for that user later.[3]


Yes, you absolutely should.

While you could hardcode the plan codes in your config.py, saving them to a local database table is the professional approach. Here is why it’s better and how to implement it:

1. Why you should save them locally

Performance: You can display your pricing page instantly without waiting for a Paystack API response.

Feature Mapping: Paystack only stores the "price" and "interval." Your database can store the features (e.g., "nexus" gets 10 projects, "flux" gets unlimited).

Data Integrity: You can create a foreign key relationship between your Subscriptions table and your Plans table.

Dynamic Updates: If you decide to add a third plan (e.g., "spark") later, you can just click a "Sync Plans" button in your admin panel instead of redeploying code.

2. Proposed Database Schema

You should create a Plan model that mirrors the Paystack data but adds your own application-specific fields.

code
Python
download
content_copy
expand_less
class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)        # nexus, flux, spark
    plan_code = Column(String, unique=True)   # PLN_wfc5nh...
    amount = Column(Integer)                  # Store in kobo (e.g., 1500000)
    interval = Column(String)                # monthly, annually
    currency = Column(String, default="NGN")
    
    # App-specific fields (Not in Paystack)
    is_active = Column(Boolean, default=True)
    features = Column(JSON)                   # ["Unlimited Storage", "Priority Support"]
    max_users = Column(Integer)               # Internal limit for your logic
3. Implementation Plan: The "Sync" Script

Create a utility function or a background task to keep your local database in sync with Paystack.

code
Python
download
content_copy
expand_less
import httpx

async def sync_paystack_plans(db: Session):
    url = "https://api.paystack.co/plan"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        paystack_plans = response.json()["data"]
        
        for p in paystack_plans:
            # Check if plan exists
            db_plan = db.query(Plan).filter(Plan.plan_code == p["plan_code"]).first()
            
            if db_plan:
                # Update existing plan (price/name might have changed)
                db_plan.amount = p["amount"]
                db_plan.name = p["name"]
            else:
                # Create new plan
                new_plan = Plan(
                    name=p["name"],
                    plan_code=p["plan_code"],
                    amount=p["amount"],
                    interval=p["interval"],
                    currency=p["currency"]
                    # set default features here
                )
                db.add(new_plan)
        
        db.commit()
4. How this changes your Subscription Flow

Now, instead of passing a string to your initialization endpoint, you use the database ID.

Before: POST /subscribe/nexus
After: POST /subscribe/{plan_id}

code
Python
download
content_copy
expand_less
@app.post("/subscribe/{plan_id}")
async def start_subscription(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Use the plan_code from the DB to initialize Paystack
    res = await initialize_subscription(current_user.email, plan.plan_code)
    return res
5. Important Warning: Price Changes

If you change a plan's price on Paystack:

Existing subscribers are not affected. They will continue to pay the old price they signed up with.

New subscribers will pay the new price.

Local DB: Your local plans table should be updated (via the sync script) so that your pricing page shows the correct new price to potential customers.

Recommendation:

Create the table.

Add a "Sync" endpoint (protected for admins only).

Manually add "features" to the rows in the database after syncing, or create a simple Admin UI to manage the extra metadata.
