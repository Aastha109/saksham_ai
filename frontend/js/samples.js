/**
 * Pre-configured prompt samples demonstrating common inefficiencies
 * and prompt optimization scenarios.
 */
window.PROMPT_SAMPLES = {
  customer_support_bloated: {
    title: "Bloated Customer Support (High Filler & Vagueness)",
    model: "gpt-4o",
    prompt: "Hello there, please kindly can you help me with this customer issue? I would really appreciate it if you could take a look at what they wrote and help me understand what is going on. They said: 'My order #99482 arrived yesterday but the blue widget was completely broken and shattered in pieces.' Please kindly do your best to make it good and tell me what we should do next, and please feel free to give any thoughts if possible. Thank you so much in advance, I really need your help!"
  },
  json_extraction_polite: {
    title: "Polite Data Extraction (Overkill on GPT-4o)",
    model: "gpt-4o",
    prompt: "Hi there! I would really like you to please kindly extract the user's name, email address, and order total from the following text: 'Customer John Doe (email: john.doe@example.com) completed transaction for $149.50 on October 10th.' Please make sure that you extract these three fields carefully. Please kindly format it as JSON. Thank you very much!"
  },
  vague_code_bug: {
    title: "Vague Code Review (High Follow-up Risk)",
    model: "claude-3-5-sonnet",
    prompt: "Here is my code for user auth: def login(u, p): return True. Can you please help me with this and make it better? It doesn't feel right and I want you to fix it and do something with security please kindly thanks."
  },
  complex_system_architecture: {
    title: "Complex Distributed Architecture (Legitimate Flagship)",
    model: "gpt-4o",
    prompt: "Design a high-throughput, horizontally scalable event-driven architecture for real-time stock ticker order processing (100k events/sec). Specify:\n1. Ingestion layer with partition rebalancing strategy\n2. Idempotent storage mechanism avoiding duplicate fills\n3. Low-latency state store for order book depth\n4. Disaster recovery and failover RPO/RTO bounds."
  },
  clean_optimized_prompt: {
    title: "Optimized Prompt (High Efficiency & Zero Fluff)",
    model: "gpt-4o-mini",
    prompt: "Task: Extract customer transaction metadata.\nInput: 'Order #49281 confirmed by Jane Smith for $89.00 on 2026-10-11.'\nConstraints:\n- Output strictly valid JSON matching schema: {\"order_id\": string, \"customer\": string, \"amount_usd\": number, \"date\": string}\n- Omit markdown code fences and conversational preamble."
  }
};
