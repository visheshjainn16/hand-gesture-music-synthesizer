import cv2
import mediapipe as mp
import math
import numpy as np
import sounddevice as sd

# --- MediaPipe setup ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(0)

# --- Audio setup ---
sample_rate = 44100
current_freq = 440.0
current_volume = 0.0
freq2 = 440.0
volume2 = 0.0
wave_type1 = "sine"
wave_type2 = "sine"
phase = 0.0

def generate_wave(wave_type, freq, t):
    if wave_type == "sine":
        return np.sin(2 * np.pi * freq * t)
    elif wave_type == "square":
        return np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == "sawtooth":
        return 2 * (t * freq - np.floor(t * freq + 0.5))
    elif wave_type == "triangle":
        saw = 2 * (t * freq - np.floor(t * freq + 0.5))
        return 2 * np.abs(saw) - 1
    else:
        return np.sin(2 * np.pi * freq * t)

def audio_callback(outdata, frames, time, status):
    global phase
    t = (np.arange(frames) + phase) / sample_rate
    wave1 = generate_wave(wave_type1, current_freq, t) * current_volume
    wave2 = generate_wave(wave_type2, freq2, t) * volume2
    outdata[:, 0] = wave1 + wave2
    phase += frames

stream = sd.OutputStream(channels=1, samplerate=sample_rate, callback=audio_callback)
stream.start()

# --- Mapping ranges ---
DIST_MIN, DIST_MAX = 20, 250
VOL_MIN, VOL_MAX = 0.0, 0.3
HEIGHT_MIN, HEIGHT_MAX = 50, 600
SMOOTHING = 0.3

NOTES = [
    ("C4", 261.63), ("D4", 293.66), ("E4", 329.63), ("F4", 349.23),
    ("G4", 392.00), ("A4", 440.00), ("B4", 493.88),
    ("C5", 523.25), ("D5", 587.33), ("E5", 659.25), ("F5", 698.46),
    ("G5", 783.99), ("A5", 880.00), ("B5", 987.77), ("C6", 1046.50)
]

INSTRUMENT_MAP = {
    1: "Warm Tone",
    2: "Bright Tone",
    3: "Buzzy Tone",
    4: "Soft Tone",
    5: "Synth Lead"
}

INSTRUMENT_WAVEFORM = {
    "Warm Tone": "triangle",
    "Bright Tone": "sawtooth",
    "Buzzy Tone": "square",
    "Soft Tone": "sine",
    "Synth Lead": "sawtooth"
}

def map_range(value, in_min, in_max, out_min, out_max):
    value = max(min(value, in_max), in_min)
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)

def count_fingers(hand_landmarks):
    landmarks = hand_landmarks.landmark
    fingers_up = 0

    if landmarks[4].x < landmarks[3].x:
        fingers_up += 1

    finger_tips = [8, 12, 16, 20]
    finger_knuckles = [6, 10, 14, 18]
    for tip, knuckle in zip(finger_tips, finger_knuckles):
        if landmarks[tip].y < landmarks[knuckle].y:
            fingers_up += 1

    return fingers_up

def freq_to_color(freq, freq_min=200, freq_max=1100):
    hue = int(map_range(freq, freq_min, freq_max, 0, 179))
    hsv_color = np.uint8([[[hue, 255, 255]]])
    bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)
    return tuple(int(c) for c in bgr_color[0][0])

# Smoothed tracking values for up to 2 hands
smooth_dist = [0.0, 0.0]
smooth_height = [0.0, 0.0]

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    h, w, _ = frame.shape
    volume2 = 0.0
    glow_color = (50, 50, 50)  # default border color when no hand detected

    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            if i > 1:
                break

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            thumb_tip = hand_landmarks.landmark[4]
            index_tip = hand_landmarks.landmark[8]

            thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
            index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)

            distance = math.hypot(index_x - thumb_x, index_y - thumb_y)
            pitch_height = h - index_y

            smooth_dist[i] += SMOOTHING * (distance - smooth_dist[i])
            smooth_height[i] += SMOOTHING * (pitch_height - smooth_height[i])

            note_index = int(map_range(smooth_height[i], HEIGHT_MIN, HEIGHT_MAX, 0, len(NOTES) - 1))
            note_name, freq = NOTES[note_index]
            vol = map_range(smooth_dist[i], DIST_MIN, DIST_MAX, VOL_MIN, VOL_MAX)

            finger_count = count_fingers(hand_landmarks)
            instrument = INSTRUMENT_MAP.get(finger_count, "Synth Lead")

            cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (255, 0, 255), 3)

            if i == 0:
                current_freq, current_volume = freq, vol
                wave_type1 = INSTRUMENT_WAVEFORM.get(instrument, "sine")
                glow_color = freq_to_color(freq)

                info_text = [
                    f"Note: {note_name}",
                    f"Frequency: {int(freq)} Hz",
                    f"Volume: {vol:.2f}",
                    f"Instrument: {instrument} (Fingers: {finger_count})"
                ]
                for idx, line in enumerate(info_text):
                    cv2.putText(frame, line, (10, 40 + idx * 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            else:
                freq2, volume2 = freq, vol
                wave_type2 = INSTRUMENT_WAVEFORM.get(instrument, "sine")

                info_text2 = [
                    f"Hand 2 Note: {note_name}",
                    f"Frequency: {int(freq)} Hz",
                    f"Volume: {vol:.2f}",
                    f"Instrument: {instrument}"
                ]
                for idx, line in enumerate(info_text2):
                    cv2.putText(frame, line, (w - 320, 40 + idx * 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 150, 0), 2)
    else:
        current_volume = 0.0
        volume2 = 0.0

    # Colored border based on pitch
    cv2.rectangle(frame, (0, 0), (w, h), glow_color, 25)

    cv2.imshow("Gesture Synth", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

stream.stop()
cap.release()
cv2.destroyAllWindows()