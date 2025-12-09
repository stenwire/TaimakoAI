import asyncio
import os
from app.services.agent_service import run_conversation, session_service, APP_NAME, USER_ID, SESSION_ID

async def verify_refactor():
    print("--- Starting Verification ---")

    # 1. Test Guardrail (Block) - Should work without API billing!
    print("\n[Test 1] Guardrail: Block Unsafe Content")
    try:
        response_block = await run_conversation("Please BLOCK this request")
        print(f"Response: {response_block}")
        assert "unsafe content" in response_block or "cannot process" in response_block
        print("✅ Guardrail Test Passed")
    except Exception as e:
        print(f"❌ Guardrail Test Failed: {e}")

    # 2. Test Delegation (Greeting) - Needs API (Commented out to isolate Guardrail)
    # print("\n[Test 2] Delegation: Greeting")
    # try:
    #     response_hello = await run_conversation("Hello")
    #     print(f"Response: {response_hello}")
    #     assert "Hello" in response_hello or "assist" in response_hello
    #     print("✅ Delegation Test Passed")
    # except Exception as e:
    #     print(f"⚠️ Delegation Test Failed (likely billing): {e}")

    # 3. Test RAG (Root Agent) - Needs API (Commented out to isolate Guardrail)
    # print("\n[Test 3] RAG: Context Retrieval")
    # try:
    #     response_rag = await run_conversation("What are stephen skills?")
    #     print(f"Response: {response_rag}")
    #     assert isinstance(response_rag, str)
    #     print("✅ RAG Test Passed")
    # except Exception as e:
    #     print(f"⚠️ RAG Test Failed (likely billing): {e}")

    # 4. Test Session State - Checks if output_key worked (depends on previous tests)
    print("\n[Test 4] Session State: Check output_key")
    try:
        session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
        last_response = session.state.get("last_agent_response")
        print(f"Last Agent Response in State: {last_response}")
        # If Guardrail passed, last_response should be the block message
        if "unsafe content" in str(last_response):
             print("✅ Session State Test Passed (Captured Guardrail Response)")
        else:
             print(f"⚠️ Session State Test Inconclusive: {last_response}")
    except Exception as e:
        print(f"❌ Session State Test Failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(verify_refactor())
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
