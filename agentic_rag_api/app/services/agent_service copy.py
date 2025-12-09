import google.generativeai as genai
from app.core.config import settings
from app.services.rag_service import rag_service
from app.models.chat import ChatResponse

class AgentService:
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("WARNING: GOOGLE_API_KEY not set. Agent will not work.")

    async def chat(self, message: str) -> ChatResponse:
        if not self.model:
            return ChatResponse(response="Agent not configured (missing API Key).", sources=[])

        # Retrieve context
        context_chunks = rag_service.query(message)
        context_text = "\n\n".join(context_chunks)
        
        prompt = f"""You are a helpful customer support agent. Use the following context to answer the user's question.
        If the answer is not in the context, say you don't know.
        
        Context:
        {context_text}
        
        User Question: {message}
        """
        
        response = self.model.generate_content(prompt)
        return ChatResponse(response=response.text, sources=context_chunks)

agent_service = AgentService()
