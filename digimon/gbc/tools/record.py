"""롬 소리 녹음 → wav (PyBoy). python3 tools/record.py 제목.wav 초 [state 파일]"""
import sys, os, wave
import numpy as np
from pyboy import PyBoy
out, sec = sys.argv[1], float(sys.argv[2])
pb = PyBoy(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'digimon.gbc'), window='null', cgb=True, sound_emulated=True, sound_sample_rate=32768)
pb.set_emulation_speed(0)
if len(sys.argv) > 3:
    with open(sys.argv[3], 'rb') as f: pb.load_state(f)
buf = []
for i in range(int(sec * 59.73)):
    pb.tick(1, True); buf.append(pb.sound.ndarray.copy())
pb.stop(save=False)
s = np.concatenate(buf).astype(np.float32)
s -= s.mean(0)
s = np.clip(s / (np.abs(s).max() + 1e-6) * 26000, -32767, 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(32768); w.writeframes(s.tobytes())
print(out, s.shape, 'peak', int(np.abs(s).max()))
