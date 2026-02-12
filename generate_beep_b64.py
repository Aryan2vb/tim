import math
import struct
import base64

def generate_beep():
    sample_rate = 16000
    duration = 0.5  # seconds
    frequency = 440.0  # Hz

    samples = []
    for i in range(int(sample_rate * duration)):
        t = float(i) / sample_rate
        # Sine wave
        sample = 32767.0 * math.sin(2.0 * math.pi * frequency * t)
        samples.append(int(sample))

    # Pack as 16-bit little-endian PCM
    pcm_data = b"".join(struct.pack("<h", s) for s in samples)

    b64_encoded = base64.b64encode(pcm_data).decode("utf-8")
    return b64_encoded

if __name__ == "__main__":
    print(generate_beep())
