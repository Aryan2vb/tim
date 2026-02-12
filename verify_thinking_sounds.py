import json
import base64
import os

def verify_thinking_sounds():
    print("Verifying thinking_sounds.json...")
    
    thinking_audio_bytes = []
    try:
        if not os.path.exists("thinking_sounds.json"):
            print("Error: thinking_sounds.json not found!")
            return

        with open("thinking_sounds.json", "r") as f:
            config = json.load(f)
            
            def add_sounds(category):
                count = 0
                for item in config.get(category, []):
                    b64_str = item.get("audio_base64", "")
                    if b64_str:
                        try:
                            decoded = base64.b64decode(b64_str)
                            if len(decoded) > 0:
                                thinking_audio_bytes.append(decoded)
                                count += 1
                        except Exception as e:
                            print(f"Failed to decode sound '{item.get('text')}': {e}")
                print(f"Loaded {count} sounds from category '{category}'.")

            add_sounds("simple")
            add_sounds("acknowledgment")
            
            print(f"Total valid audio clips loaded: {len(thinking_audio_bytes)}")
            
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in thinking_sounds.json")
    except Exception as e:
        print(f"Error loading thinking_sounds.json: {e}")

if __name__ == "__main__":
    verify_thinking_sounds()
