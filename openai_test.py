import openai

# Use your existing API key
openai_key = "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"
client = openai.OpenAI(api_key=openai_key)

prompt = (
    "Format your answer EXACTLY as in the example below:\n"
    "------------------------\n"
    "Question: What is the function of FTP?\n"
    "A (0%) Email service\n"
    "B (0%) Directory access\n"
    "C (0%) Serving of web pages\n"
    "D (100%) File exchange\n"
    "------------------------\n"
    "At the bottom, present all answers and their % in this format: A:0%, B:0%, C:0%, D:100%\n"
    "------------------------\n"
    "REMEMBER: Output ONLY in the format shown above. Do not include any extra text or explanation."
)

print("----- PROMPT SENT TO AI -----")
print(prompt)
print("----- AI RESPONSE -----")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
)
print(response.choices[0].message.content)