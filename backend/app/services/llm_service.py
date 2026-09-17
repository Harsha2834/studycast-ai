import json
import re
import requests

from ..config import OLLAMA_URL, OLLAMA_MODEL


def fallback(text, speaker_a, speaker_b):
    sentences = [
        x.strip()
        for x in re.split(r"(?<=[.!?])\s+", text)
        if len(x.strip()) > 25
    ][:8]

    if not sentences:
        sentences = [
            "The uploaded material contains a topic that we can break into simple parts."
        ]

    conversation = []

    for i, sentence in enumerate(sentences):
        speaker = speaker_a if i % 2 == 0 else speaker_b

        prefix = (
            "The key idea is: "
            if i % 2 == 0
            else "In simple words: "
        )

        conversation.append({
            "speaker": speaker,
            "text": prefix + sentence
        })

    return conversation


def generate(text, preferences):

    speaker_a = preferences.get("speaker_a", "Alex")
    speaker_b = preferences.get("speaker_b", "Maya")

    context = text[:12000]

    # JSON schema that Ollama must follow
    schema = {
        "type": "object",
        "properties": {
            "conversation": {
                "type": "array",
                "minItems": 8,
                "maxItems": 16,
                "items": {
                    "type": "object",
                    "properties": {
                        "speaker": {
                            "type": "string"
                        },
                        "text": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "speaker",
                        "text"
                    ]
                }
            }
        },
        "required": [
            "conversation"
        ]
    }

    prompt = f"""
You are generating a podcast-style study conversation.

Create a conversation between exactly two speakers:

Speaker 1: {speaker_a}
Speaker 2: {speaker_b}

IMPORTANT RULES:

1. Generate between 8 and 16 conversation turns.
2. Return a JSON object containing a field named "conversation".
3. The "conversation" field must contain an array.
4. Every array item must contain:
   - "speaker"
   - "text"
5. Alternate between {speaker_a} and {speaker_b}.
6. Use ONLY information from the study material.
7. Do not give a summary outside the conversation.
8. Make the conversation natural and engaging.
9. Explain concepts according to the requested preferences.
10. Do not stop after one response.

Preferences:

Style: {preferences.get("style")}
Level: {preferences.get("level")}
Language: {preferences.get("language")}
Tone: {preferences.get("tone")}
Instruction: {preferences.get("prompt")}

STUDY MATERIAL:

{context}
"""

    try:

        print("\n===================================")
        print("Calling Ollama:", OLLAMA_URL)
        print("Using model:", OLLAMA_MODEL)
        print("===================================\n")

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": 0.7
                }
            },
            timeout=300
        )

        response.raise_for_status()

        raw = response.json()["message"]["content"]

        print("\n========== OLLAMA RAW RESPONSE ==========")
        print(raw)
        print("=========================================\n")

        data = json.loads(raw)

        print("OLLAMA PARSED DATA TYPE:", type(data))
        print("OLLAMA PARSED DATA:", data)

        if not isinstance(data, dict):
            raise ValueError(
                "Ollama response is not a JSON object"
            )

        if "conversation" not in data:
            raise ValueError(
                "Ollama response does not contain 'conversation'"
            )

        conversation = data["conversation"]

        if not isinstance(conversation, list):
            raise ValueError(
                "'conversation' is not a JSON array"
            )

        output = []

        for i, item in enumerate(conversation):

            if not isinstance(item, dict):
                continue

            generated_text = str(
                item.get("text", "")
            ).strip()

            if not generated_text:
                continue

            # Force alternating speakers
            speaker = (
                speaker_a
                if i % 2 == 0
                else speaker_b
            )

            output.append({
                "speaker": speaker,
                "text": generated_text
            })

        print("VALID CONVERSATION TURNS:", len(output))

        if len(output) < 2:
            raise ValueError(
                f"Not enough conversation turns: {len(output)}"
            )

        print("Successfully generated conversation using Ollama")

        return output, "ollama"

    except Exception as e:

        print("\n===================================")
        print("OLLAMA ERROR")
        print("Error type:", type(e).__name__)
        print("Error:", repr(e))
        print("Using fallback script instead.")
        print("===================================\n")

        return fallback(
            context,
            speaker_a,
            speaker_b
        ), "fallback"