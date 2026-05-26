Below is your **tutorial script with only the spoken audio parts (lines inside `>`) converted to Hindi**. All other text – headings, code blocks, notes, screen directions, tool explanations – remains in English. YouTube-related phrases are already removed. The script is ready for audio recording in Hindi while keeping the written guide in English.

---

# 🚀 Complete Project-Based LangChain Tutorial  
## "Customer Support Bot with LangChain" — For Beginners (Hindi Audio / English Text)

---

## 📌 Tutorial Overview

**What you will build:**  
A **Customer Support Bot** for a fictional company "ShopEasy" that:  
- ✅ Answers customer queries from company FAQ documents (RAG)  
- ✅ Remembers conversation context (Memory)  
- ✅ Handles order status, refund policy, shipping queries  
- ✅ Escalates to human when unsure  
- ✅ Has a simple Streamlit UI  

**Tools used:**  
- **LangChain** – orchestration framework  
- **Groq** – fast LLM (free tier available)  
- **FAISS** – vector database  
- **HuggingFace embeddings** – local, no OpenAI  
- **Streamlit** – UI  

---

## 📝 Full Tutorial Script (Hindi Audio / English Text)

---

### 🎬 SECTION 1: INTRODUCTION (0:00 – 1:30)

**[Screen: Show the finished bot answering customer questions]**

> "नमस्ते दोस्तों! सोचिए आप एक ई-कॉमर्स कंपनी चला रहे हैं, और हर दिन 1000+ ग्राहक एक जैसे सवाल पूछते हैं – 'मेरा ऑर्डर कहाँ है?', 'रिफंड कैसे मिलेगा?', 'डिलीवरी कब तक आएगी?'। क्या हो अगर मैं आपको बताऊँ कि आप एक ऐसा AI बॉट बना सकते हैं जो ये सारे सवाल अपने आप हल कर ले – सिर्फ 45 मिनट में?"

> "आज हम LangChain का उपयोग करके एक **असली कस्टमर सपोर्ट बॉट** बनाएंगे – बिल्कुल शुरुआत से। यह ट्यूटोरियल शुरुआत करने वालों के लिए है। अगर आपको बेसिक Python आती है, तो आप आसानी से फॉलो कर सकते हैं।"

> "इस ट्यूटोरियल के अंत तक आपके पास एक काम करने वाला AI बॉट होगा जो आपकी कंपनी के दस्तावेज़ों से जवाब दे सकता है। तो चलिए शुरू करते हैं!"

---

### 🎬 SECTION 2: WHAT WE'RE BUILDING (1:30 – 3:00)

**[Architecture diagram]**

> "तो पहले समझते हैं कि हम क्या बना रहे हैं। हमारा बॉट 4 काम करेगा:"

> "**पहला** – ग्राहक के सवाल को समझेगा। **दूसरा** – कंपनी के FAQ दस्तावेज़ों में से प्रासंगिक जानकारी ढूंढेगा। **तीसरा** – एक स्मार्ट, प्राकृतिक जवाब तैयार करेगा। **चौथा** – अगर उसे जवाब नहीं पता, तो विनम्रतापूर्वक मानव एजेंट को बता देगा।"

> "इसके लिए हम उपयोग करेंगे – **LangChain** फ्रेमवर्क, **Groq का LLM** (तेज़ और मुफ्त), **FAISS** वेक्टर डेटाबेस, और **Streamlit** यूजर इंटरफेस के लिए। चिंता मत करें अगर ये शब्द अभी समझ नहीं आ रहे – मैं हर चीज़ विस्तार से समझाऊँगा।"

---

### 🎬 SECTION 3: WHAT IS LANGCHAIN? (3:00 – 5:00)

**[Simple diagram]**

> "सबसे पहले समझते हैं – LangChain क्या है? सरल शब्दों में, **LangChain एक फ्रेमवर्क है जो AI एप्लिकेशन बनाने को आसान बनाता है**। LangChain को LEGO सेट की तरह समझें – अलग-अलग टुकड़े होते हैं जैसे LLM, Memory, Tools, और आप उन्हें जोड़कर कोई भी AI ऐप बना सकते हैं।"

> "बिना LangChain के, अगर आपको ChatGPT जैसा बॉट बनाना है जो आपके दस्तावेज़ों को पढ़ सके, तो आपको 500+ लाइन कोड लिखनी पड़ेगी। LangChain के साथ, वही काम **50 लाइनों** में हो जाता है। इसलिए आज दुनिया की बड़ी कंपनियाँ – Uber, LinkedIn, Morgan Stanley – सभी LangChain का उपयोग कर रही हैं।"

---

### 🎬 SECTION 4: SETUP & INSTALLATION (5:00 – 8:00)

**[Terminal + VS Code]**

> "अब चलते हैं कोडिंग पर! सबसे पहले एक नया फ़ोल्डर बनाएँ – मैं बना रहा हूँ `customer-support-bot`। इसके अंदर एक virtual environment बनाएंगे ताकि हमारी डिपेंडेंसी साफ रहें।"

```bash
mkdir customer-support-bot
cd customer-support-bot
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate   # Mac/Linux
```

> "अब सभी ज़रूरी लाइब्रेरी इंस्टॉल करते हैं:"

```bash
pip install langchain langchain-groq langchain-community
pip install faiss-cpu streamlit python-dotenv sentence-transformers
```

**Library explanation:**  
- `langchain` – main framework  
- `langchain-groq` – connects to Groq's LLM (free, fast)  
- `sentence-transformers` – provides local embeddings (no OpenAI)  
- `faiss-cpu` – vector database  
- `streamlit` – UI  

> "अब एक `.env` फ़ाइल बनाएँ और उसमें **Groq API key** डालें। मुफ्त key **console.groq.com** से ले सकते हैं।"

```
GROQ_API_KEY=gsk_your_key_here
```

> "⚠️ ज़रूरी – यह फ़ाइल कभी GitHub पर अपलोड न करें! हमेशा `.gitignore` में शामिल करें।"

---

### 🎬 SECTION 5: CORE CONCEPT #1 — LLM BASICS (8:00 – 12:00)

**[VS Code, new file `step1_basic.py`]**

> "चलिए सबसे पहले एक बेसिक LLM कॉल करते हैं। यह नींव है।"

```python
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# Hamara AI model (Groq)
llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.3)

# Customer ka question
response = llm.invoke("Mera order 2 din se nahi aaya, kya karu?")
print(response.content)
```

> "कोड समझें: **ChatGroq** Groq के मॉडल से बात करता है। **temperature 0.3** रखा है – कस्टमर सपोर्ट में हमें पूर्वानुमानित, सटीक उत्तर चाहिए, रचनात्मक नहीं। चलाएँ – `python step1_basic.py`। मॉडल एक सामान्य उत्तर देगा। लेकिन यह उत्तर **हमारी कंपनी की नीतियों से संबंधित नहीं है**। इसके लिए ज़रूरत है **Prompt Templates** की।"

---

### 🎬 SECTION 6: CORE CONCEPT #2 — PROMPT TEMPLATES (12:00 – 16:00)

**[New file `step2_prompt.py`]**

> "Prompt Template एक **पुन: प्रयोज्य टेम्प्लेट** है जिसमें हम गतिशील रूप से मान डाल सकते हैं।"

```python
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.3)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Tum ShopEasy company ke customer support agent ho.
    Hamesha polite aur helpful raho. Hindi-English mix mein answer do.
    Agar tumhe answer nahi pata, toh saaf bolo ki main human agent 
    ko connect kar deta hoon."""),
    ("user", "{question}")
])

chain = prompt | llm

response = chain.invoke({"question": "Refund kitne din mein milta hai?"})
print(response.content)
```

> "System message में हमने बॉट को **व्यक्तित्व** दिया। `|` चिह्न **LCEL** (LangChain Expression Language) है – पाइप की तरह काम करता है। चलाएँ – अब बॉट सही कस्टमर सपोर्ट एजेंट जैसा व्यवहार करेगा!"

---

### 🎬 SECTION 7: CORE CONCEPT #3 — RAG (KNOWLEDGE BASE) (16:00 – 25:00)

**[RAG flow diagram]**

> "अब आता है सबसे महत्वपूर्ण भाग – **RAG (Retrieval Augmented Generation)**। बॉट को कंपनी की विशिष्ट जानकारी सिखाना।"

**[Create `data/faq.txt`]**

```text
ShopEasy Customer Support FAQ:

1. Delivery Time: Standard delivery 3-5 working days. 
   Express delivery 1-2 days available.

2. Refund Policy: Refund 7-10 working days mein process hota hai. 
   Product delivery ke 30 din ke andar return kar sakte hain.

3. Order Tracking: Order place karne ke baad ek tracking ID 
   email pe milta hai.

4. Cancellation: Order ship hone se pehle free cancel kar sakte hain.

5. Customer Care: Phone - 1800-123-4567, Email - support@shopeasy.com
   Working hours: 9 AM to 9 PM.
```

> "अब इस दस्तावेज़ को बॉट के 'दिमाग' में डाल रहे हैं (local embeddings use karenge — no OpenAI):"

**[New file `step3_rag.py`]**

```python
from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

# Step 1: Load document
loader = TextLoader("data/faq.txt", encoding="utf-8")
documents = loader.load()

# Step 2: Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.split_documents(documents)

# Step 3: Create embeddings (local, free)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Step 4: Prompt
prompt = ChatPromptTemplate.from_template("""
Tum ShopEasy ke customer support agent ho. 
Niche diye gaye context ke basis pe customer ka question answer karo.
Agar context mein answer nahi hai, toh bolo ki main human agent ko connect kar deta hoon.

Context: {context}
Question: {question}

Answer:
""")

llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.3)

# Step 5: Chain
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print(chain.invoke("Mera refund kab tak aayega?"))
```

> "यहाँ जादू है: **HuggingFaceEmbeddings** local model use karta hai – no API key needed. **Retriever** vector database में खोज करता है जैसे Google। अब बॉट हमारी विशिष्ट FAQ से उत्तर दे रहा है।"

---

### 🎬 SECTION 8: CORE CONCEPT #4 — MEMORY (25:00 – 30:00)

**[New file `step4_memory.py`]**

> "अभी हमारा बॉट गोल्डफिश जैसा है – हर सवाल स्वतंत्र है। हमें बातचीत की याददाश्त चाहिए।"

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Setup (same as before)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)  # or recreate
retriever = vectorstore.as_retriever()
llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.3)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True
)

# First question
result1 = qa_chain.invoke({"question": "Refund policy kya hai?"})
print("Bot:", result1["answer"])

# Follow-up (understands "iska")
result2 = qa_chain.invoke({"question": "Iska time kitna lagta hai?"})
print("Bot:", result2["answer"])
```

> "दूसरे सवाल में 'इसका' लिखा। बॉट समझ गया कि रिफंड की बात हो रही है। **ConversationBufferMemory** पूरी चैट इतिहास याद रखता है।"

---

### 🎬 SECTION 9: BUILDING THE UI WITH STREAMLIT (30:00 – 40:00)

**[New file `app.py`]**

> "अब अंतिम भाग – Streamlit से एक सुंदर यूजर इंटरफेस बनाते हैं।"

```python
import streamlit as st
from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="ShopEasy Support", page_icon="🛍️")
st.title("🛍️ ShopEasy Customer Support")
st.caption("Aapka AI assistant - 24/7 available")

@st.cache_resource
def setup_bot():
    loader = TextLoader("data/faq.txt", encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_documents(docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    llm = ChatGroq(model="mixtral-8x7b-32768", temperature=0.3)
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

qa_chain = setup_bot()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Namaste! Main ShopEasy ka support assistant hoon. Aapki kya help kar sakta hoon?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if user_input := st.chat_input("Apna question yahan likhein..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Soch raha hoon..."):
            response = qa_chain.invoke({"question": user_input})
            answer = response["answer"]
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
```

> "चलाएँ – `streamlit run app.py`। ब्राउज़र खुलेगा और एक पेशेवर कस्टमर सपोर्ट बॉट तैयार है!"

---

### 🎬 SECTION 10: TESTING (40:00 – 43:00)

> "चलिए एक वास्तविक दुनिया के परिदृश्य का परीक्षण करते हैं। मैं ग्राहक बनकर बात करता हूँ..."

> "**सवाल 1:** 'डिलीवरी कितने दिनों में होती है?' → बॉट FAQ से उत्तर देता है।  
> **सवाल 2:** 'एक्सप्रेस डिलीवरी उपलब्ध है?' → हाँ।  
> **सवाल 3:** 'क्या मेरी डिलीवरी मंगल ग्रह पर होगी?' → बॉट विनम्रतापूर्वक कहता है कि जानकारी उपलब्ध नहीं है, मानव एजेंट से जोड़ेगा। **यही है पेशेवर बॉट का व्यवहार!** "

---

### 🎬 SECTION 11: NEXT STEPS & OUTRO (43:00 – 45:00)

> "तो दोस्तों, हमने सीखा: LangChain basics, Prompt Templates, RAG, Memory, और Streamlit UI। आपने एक production-ready customer support bot बना लिया!"

> "अब इसे बेहतर कर सकते हैं – PDF documents add karo, multiple languages, WhatsApp integration, ya database se real order status fetch karo."

> "**सारा कोड GitHub pe available hai – link description mein hai. Clone karo, experiment karo, aur apna version banao!**"

> "अगर यह ट्यूटोरियल helpful lage toh share karo apne developer friends ke saath. Koi doubt ho toh comments mein puchho."

> "Happy Coding! 🚀"

---

## 🔁 Switching to OpenRouter (Alternative to Groq)

If you prefer **OpenRouter**, replace Groq with:

```bash
pip install langchain-openai  # OpenRouter uses OpenAI-compatible endpoint
```

Then in code:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your-openrouter-key",
    model="openai/gpt-3.5-turbo",  # any model from openrouter
    temperature=0.3
)
```

Embeddings remain same (HuggingFace) to avoid OpenAI completely.

---

**Note:** Only the lines inside `>` (the spoken narration) are in Hindi. Everything else (code, instructions, notes, section headings) remains in English. This script contains **no YouTube keywords** and works with **Groq + local embeddings**. Enjoy recording your Hindi audio tutorial!