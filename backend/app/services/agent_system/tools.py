from typing import Optional
from google.adk.tools.tool_context import ToolContext
from app.services.agent_system.tool_schemas import (
    GetContextInput, ContextOutput,
    SayHelloInput, GreetingOutput,
    FarewellOutput
)
from app.db.session import SessionLocal
from app.models.business import Business
from app.models.product import Product
from app.models.escalation import Escalation, EscalationStatus
from app.models.chat_session import ChatSession
from app.services.email_service import EmailServiceFactory
from app.services.agent_system.tool_schemas import (
    AnalyzeSentimentInput, AnalyzeSentimentOutput,
    EscalateToHumanInput, EscalateToHumanOutput,
    SearchProductsInput, SearchProductsOutput, ProductToolSchema,
    CreateOrderInput, CreateOrderOutput,
)
import json
from decimal import Decimal
from app.core.subscription import TIER_LIMITS
from app.core.config import settings


try:
    from google import genai
except ImportError:
    genai = None

# Mock RAG Service import (handling missing dependencies as done previously)
try:
    from app.services.rag_service import rag_service
except ImportError:
    print("Warning: RAG Service dependencies missing. Using Mock RAG Service.")
    class MockRAGService:
        def query(self, text, user_id=None, api_key=None):
            return [f"Mock context for: {text}"]
    rag_service = MockRAGService()

def get_context(user_input: str, tool_context: ToolContext) -> str:
    """Retrieves context from the RAG service using structured schemas.

    Args:
        user_input: The user's input message.
        tool_context: The tool context to access session state.

    Returns:
        str: The retrieved context as a formatted string.
    """
    print(f"--- Tool: get_context called for user_input: {user_input} ---")
    
    # Validate input using Pydantic schema
    try:
        validated_input = GetContextInput(user_input=user_input)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"
    
    # Extract user_id from state
    user_id = tool_context.state.get("user_id")
    if not user_id:
        return "Error: User ID not found in session state."
    
    # Extract api_key from state
    api_key = tool_context.state.get("api_key")
    if not api_key:
        print(f"Warning: Tool get_context missing api_key for user {user_id}")
        return "Error: API Key configuration missing. Cannot access knowledge base."

    # Example of reading from state
    style = tool_context.state.get("response_style", "normal")
    print(f"--- Tool: Reading state 'response_style': {style} ---")
    print(f"--- Tool: Using user_id: {user_id} ---")

    # Retrieve context with user_id and api_key
    context_chunks = rag_service.query(text=validated_input.user_input, user_id=user_id, api_key=api_key)
    print(f"--- Tool: RAG Service returned {len(context_chunks)} chunks ---")
    
    # Create structured output
    output = ContextOutput(
        context_text="\n\n".join(context_chunks),
        chunks_count=len(context_chunks)
    )
    
    # Return as string for ADK compatibility
    return output.context_text

def say_hello(name: Optional[str] = None) -> str:
    """Provides a greeting using structured schemas.

    Args:
        name: Optional name of the person to greet.

    Returns:
        str: A friendly greeting message.
    """
    # Validate input using Pydantic schema
    try:
        validated_input = SayHelloInput(name=name)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"
    
    if validated_input.name:
        message = f"Hello, {validated_input.name}! How can I help you today?"
    else:
        message = "Hello! How can I assist you with your questions?"
    
    # Create structured output
    output = GreetingOutput(message=message)
    return output.message

def say_goodbye() -> str:
    """Provides a farewell message using structured schemas.
    
    Returns:
        str: A polite farewell message.
    """
    # Create structured output
    output = FarewellOutput(message="Goodbye! Have a great day.")
    return output.message

def analyze_sentiment(user_text: str, tool_context: ToolContext) -> str:
    """Analyzes the sentiment of the user's text.
    
    Args:
        user_text: The input text to analyze.
        tool_context: Context containing API key.
        
    Returns:
        JSON string with sentiment and score.
    """
    print(f"--- Tool: analyze_sentiment called for: {user_text} ---")
    
    # 1. Validate Input
    try:
        validated_input = AnalyzeSentimentInput(user_text=user_text)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"

    api_key = tool_context.state.get("api_key")
    
    sentiment = "Neutral"
    score = 0.5
    
    # 2. Use Gemini if available
    if api_key and genai:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Analyze the sentiment of the following text.
            Text: "{validated_input.user_text}"
            
            Return JSON only: {{"sentiment": "Positive" | "Neutral" | "Negative", "score": 0.0 to 1.0}}
            """
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )
            text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text)
            sentiment = data.get("sentiment", "Neutral")
            score = data.get("score", 0.5)
        except Exception as e:
            print(f"Sentiment Analysis Error: {e}")
            # Fallback based on keywords
            lower_text = validated_input.user_text.lower()
            if any(w in lower_text for w in ["angry", "bad", "terrible", "hate", "scam"]):
                sentiment = "Negative"
                score = 0.9
            elif any(w in lower_text for w in ["good", "great", "love", "thanks"]):
                sentiment = "Positive"
                score = 0.9

    # 3. Return Output
    output = AnalyzeSentimentOutput(sentiment=sentiment, score=score)
    # Storing sentiment in state for other tools to use if needed
    tool_context.state["last_sentiment"] = sentiment
    
    return json.dumps(output.model_dump())

def escalate_to_human(reason: str, user_message: str, tool_context: ToolContext) -> str:
    """Escalates the conversation to a human agent.
    
    Args:
        reason: Why the escalation is happening.
        user_message: The user's message triggering it.
        
    Returns:
        Confirmation message.
    """
    print(f"--- Tool: escalate_to_human called. Reason: {reason} ---")
    
    # 1. Validate Input
    try:
        validated_input = EscalateToHumanInput(reason=reason, user_message=user_message)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"

    session_id = tool_context.state.get("session_id")
    
    if not session_id:
        session_id = tool_context.state.get("session_id")
        
    if not session_id:
        return "Error: Session ID missing from context. Cannot escalate."

    db = SessionLocal()
    try:
        # 2. Get Session and Business
        # 2. Get Session and Business using sequential queries (avoiding join ambiguity)
        print(f"Escalation: Fetching session {session_id}")
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        
        if not chat_session:
            print(f"Escalation Error: Session {session_id} not found")
            return "Error: Chat Session not found."
        
        print(f"Escalation: Session found. Guest ID: {chat_session.guest_id}")
        
        # Get guest user
        if not chat_session.guest:
            print(f"Escalation Error: No guest associated with session {session_id}")
            return "Error: Guest user not found."
        
        guest = chat_session.guest
        print(f"Escalation: Guest found. Widget ID: {guest.widget_id}")
        
        # Get widget settings
        if not guest.widget:
            print(f"Escalation Error: No widget associated with guest {guest.id}")
            return "Error: Widget not found."
        
        widget = guest.widget
        print(f"Escalation: Widget found. User ID: {widget.user_id}")
        
        # Get business via user_id
        business = db.query(Business).filter(Business.user_id == widget.user_id).first()
        
        if not business:
            print(f"Escalation Error: No business found for user {widget.user_id}")
            return "Error: Business not found."
        
        import logging
        logger = logging.getLogger(__name__)

        print(f"Escalation: Business found. Name: {business.business_name}, Escalation enabled: {business.is_escalation_enabled}")

        # 3. Check if enabled and within limits
        if not business.is_escalation_enabled:
            return "I apologize, but human escalation is currently not available for this service."
            
        # Check limits
        tier = business.subscription_tier or "spark"
        max_escalations = TIER_LIMITS.get(tier, {}).get("max_monthly_escalations", 5)
        
        if business.used_escalations >= max_escalations:
            print(f"Escalation Limit Reached for business {business.id}")
            return "I apologize, but we cannot process further escalations at this time due to high volume."

        # 4. Create Escalation
        existing_escalation = db.query(Escalation).filter(Escalation.session_id == session_id).first()
        if existing_escalation:
            escalation = existing_escalation
            logger.info(f"Escalation for session {session_id} already exists. Returning existing one.")
        else:
            escalation = Escalation(
                business_id=business.id,
                session_id=session_id,
                summary=f"Escalation Triggered: {validated_input.reason}\nUser Message: {validated_input.user_message}",
                sentiment="Negative", # Default or should be passed.
                status=EscalationStatus.PENDING.value
            )
            db.add(escalation)
            
            # Increment usage only on new creation
            business.used_escalations += 1
            db.add(business)
            
        db.commit()
        db.refresh(escalation)
        
        # 5. Send Email
        email_service = EmailServiceFactory.get_service()
        emails = business.escalation_emails or []
        if emails:
            subject = f"Escalation Alert: {business.business_name}"
            body = (
                f"New Escalation Request.\n"
                f"Session ID: {session_id}\n"
                f"Reason: {validated_input.reason}\n"
                f"User Message: {validated_input.user_message}\n"
            )
            from app.services.email_service import EmailSchema
            import asyncio
            import threading

            schema = EmailSchema(
                subject=subject,
                recipients=emails,
                body=body
            )

            def send_in_thread(coro):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(coro)
                except Exception as e:
                    print(f"Error sending escalation email: {e}")
                finally:
                    loop.close()

            threading.Thread(target=send_in_thread, args=(email_service.send_email(schema),)).start()
            
        output = EscalateToHumanOutput(
            escalation_id=escalation.id,
            status="pending",
            message="Your request has been forwarded to a human agent. Only a summary will be shared."
        )
        
        return json.dumps(output.model_dump())
        
    except Exception as e:
        print(f"Escalation Error: {e}")
        return f"Error processing escalation: {str(e)}"
    finally:
        db.close()

def search_products(query: str, tool_context: ToolContext) -> str:
    """Searches the product catalogue for items matching the query.
    
    Args:
        query: Search term (name, category, description).
        tool_context: Context containing business user_id.
        
    Returns:
        JSON string with list of matching products.
    """
    print(f"--- Tool: search_products called for: {query} ---")
    
    try:
        validated_input = SearchProductsInput(query=query)
    except Exception as e:
        return f"Error: Invalid input - {str(e)}"

    user_id = tool_context.state.get("user_id")
    if not user_id:
        return "Error: User ID not found in session state."

    db = SessionLocal()
    try:
        # 1. Find business
        business = db.query(Business).filter(Business.user_id == user_id).first()
        if not business:
            return "Error: Business not found for this session."

        # 2. Search products
        search_term = f"%{validated_input.query}%"
        products = db.query(Product).filter(
            Product.business_id == business.id,
            Product.is_active,
            (Product.name.ilike(search_term)) | 
            (Product.category.ilike(search_term)) | 
            (Product.description.ilike(search_term)) |
            (Product.sku.ilike(search_term))
        ).all()

        # 3. Format output
        product_list = [
            ProductToolSchema(
                name=p.name,
                price=float(p.price),
                currency=p.currency,
                sku=p.sku,
                description=p.description,
                stock_quantity=p.stock_quantity,
                image_urls=p.image_urls
            ) for p in products
        ]
        
        output = SearchProductsOutput(products=product_list, count=len(product_list))
        return json.dumps(output.model_dump())

    except Exception as e:
        print(f"Search Products Error: {e}")
        return f"Error searching products: {str(e)}"
    finally:
        db.close()


def create_order(
    customer_name: str,
    items: list[dict],
    tool_context: ToolContext,
    customer_email: Optional[str] = None,
    customer_phone: Optional[str] = None,
    customer_address: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Creates a new order from a customer's purchase intent.

    Args:
        customer_name: Customer's full name.
        items: List of order items. Each item is a dict with keys: product_name (str), product_sku (str), quantity (int), unit_price (float), currency (str).
        tool_context: Context containing business user_id and session_id.
        customer_email: Customer's email address.
        customer_phone: Customer's phone number.
        customer_address: Customer's shipping/delivery address.
        notes: Any additional notes.

    Returns:
        JSON string with order confirmation details.
    """
    print(f"--- Tool: create_order called for customer: {customer_name} ---")

    try:
        validated = CreateOrderInput(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            customer_address=customer_address,
            items=items,
            notes=notes,
        )
    except Exception as e:
        return f"Error: Invalid order input - {str(e)}"

    user_id = tool_context.state.get("user_id")
    session_id = tool_context.state.get("session_id")
    if not user_id:
        return "Error: User ID not found in session state."

    from app.models.order import Order, OrderItem

    db = SessionLocal()
    try:
        business = db.query(Business).filter(Business.user_id == user_id).first()
        if not business:
            return "Error: Business not found for this session."

        total = Decimal("0.00")
        order_items = []
        currency = "USD"

        for item_data in validated.items:
            qty = item_data.quantity
            unit_price = Decimal(str(item_data.unit_price))
            line_total = unit_price * qty
            total += line_total
            currency = item_data.currency

            # Try to resolve product_id by SKU
            product = db.query(Product).filter(
                Product.business_id == business.id,
                Product.sku == item_data.product_sku,
            ).first()

            order_items.append(OrderItem(
                product_id=product.id if product else None,
                product_name=item_data.product_name,
                product_sku=item_data.product_sku,
                quantity=qty,
                unit_price=unit_price,
                total_price=line_total,
                currency=currency,
            ))

        order = Order(
            business_id=business.id,
            session_id=session_id,
            customer_name=validated.customer_name,
            customer_email=validated.customer_email,
            customer_phone=validated.customer_phone,
            customer_address=validated.customer_address,
            status="pending",
            total_amount=total,
            currency=currency,
            notes=validated.notes,
        )
        db.add(order)
        db.flush()  # get order.id before adding items

        for oi in order_items:
            oi.order_id = order.id
            db.add(oi)

        db.commit()
        db.refresh(order)

        print(f"--- Tool: Order {order.id} created for business {business.id} ---")

        # Notify business owner by email
        try:
            email_service = EmailServiceFactory.get_service()
            emails = business.escalation_emails or []
            if emails:
                from app.services.email_service import EmailSchema
                import asyncio
                import threading

                item_lines = "\n".join(
                    f"  - {oi.product_name} (SKU: {oi.product_sku}) x{oi.quantity} @ {oi.unit_price} {oi.currency}"
                    for oi in order_items
                )
                body = (
                    f"New Order Received!\n\n"
                    f"Order ID: {order.id}\n"
                    f"Customer: {validated.customer_name}\n"
                    f"Email: {validated.customer_email or 'N/A'}\n"
                    f"Phone: {validated.customer_phone or 'N/A'}\n"
                    f"Address: {validated.customer_address or 'N/A'}\n\n"
                    f"Items:\n{item_lines}\n\n"
                    f"Total: {total} {currency}\n"
                )
                schema = EmailSchema(
                    subject=f"New Order from {validated.customer_name} — {business.business_name}",
                    recipients=emails,
                    body=body,
                )

                def _send(coro):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(coro)
                    except Exception as err:
                        print(f"Order email error: {err}")
                    finally:
                        loop.close()

                threading.Thread(target=_send, args=(email_service.send_email(schema),)).start()
        except Exception as email_err:
            print(f"--- Tool: Order email notification failed: {email_err} ---")

        output = CreateOrderOutput(
            order_id=order.id,
            status="pending",
            total_amount=float(total),
            currency=currency,
            message=(
                f"Your order has been placed successfully! Order ID: {order.id}. "
                f"Total: {total} {currency}. "
                f"Our team will contact you shortly to arrange payment and delivery."
            ),
        )
        return json.dumps(output.model_dump())

    except Exception as e:
        print(f"Create Order Error: {e}")
        return f"Error creating order: {str(e)}"
    finally:
        db.close()
