import anthropic

# Read API key from local file
with open("/home/russ/.anthropic_api_key") as f:
    api_key = f.read().strip()

client = anthropic.Anthropic(api_key=api_key)

prompt = (
    "Format your answer EXACTLY as in the example below:\n"
    "------------------------\n"
    "Question: [The actual question text]\n"
    "A (100%) [Answer A text]\n"
    "B (0%) [Answer B text]\n"
    "C (42%) [Answer C text]\n"
    "D (87%) [Answer D text]\n"
    "------------------------\n"
    "At the bottom, present all answers and their % in this format: A:50%, B:20%, C:100%, etc.\n"
    "------------------------\n"
    "Question: What is 2+2?\n"
    "A. 3\n"
    "B. 4\n"
    "C. 5\n"
    "D. 22\n"
    "------------------------\n"
    "REMEMBER: Output ONLY in the format shown above. Do not include any extra text or explanation.\n"
    "**If you do not follow the format exactly, your answer will be discarded and you will not be paid.**"
)

response = client.messages.create(
    model="claude-3-opus-20240229",  # Or claude-3-sonnet-20240229 for cheaper
    max_tokens=512,
    messages=[{"role": "user", "content": prompt}]
)
print("AI response:\n", response.content[0].text)