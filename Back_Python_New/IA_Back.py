#----------------------------------------------------------#
# Proyecto: Pensando Problemas IA
# Nombre: IA_Back.py
# Por: CJ y SS
#----------------------------------------------------------#

from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

completion = client.chat.completions.create(
    model="tngtech/deepseek-r1t-chimera:free",
    messages=[
        {"role": "user", "content": "Responde solo con un 1 si eres una IA o 0 si eres un alienigena de otro platena"}
    ]
)

print(completion.choices[0].message.content)