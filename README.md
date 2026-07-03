# Gesture Synth

Play music with your hands, no instrument required. This is a real-time hand gesture music synthesizer — point your webcam at yourself, move your hands around, and it turns your gestures into sound.

I built this because I wanted a project that combined computer vision with something that actually felt fun to use, not just another CV demo that draws boxes on a screen. Turns out mapping hand position to pitch and volume in real time is a pretty fun problem — it touches everything from landmark detection to audio signal generation to keeping latency low enough that it feels responsive.

## What it does

- Tracks both your hands using MediaPipe's hand landmark model
- **Vertical hand position** controls pitch (move your hand up, the note goes higher)
- **Distance between your thumb and index finger** controls volume (pinch closer = quieter, spread apart = louder)
- **Number of fingers held up** switches between five different instrument tones (sine, triangle, square, sawtooth combinations)
- Works with both hands at once, so you can play two notes simultaneously — actual two-hand harmony, not just gesture detection running twice
- The screen border glows a different color depending on the pitch you're playing, so there's some visual feedback too

## How it works

The short version: OpenCV grabs frames from your webcam, MediaPipe finds 21 landmark points per hand, and I use the coordinates of specific landmarks (thumb tip, index tip, hand height) to calculate pitch, volume, and instrument selection every frame.

The audio side runs independently of the video loop using `sounddevice`'s callback-based output stream. Every time the sound card needs more audio samples, the callback function generates a fresh chunk of waveform on the fly using the current pitch/volume/instrument values — sine, square, sawtooth, or triangle wave math, depending on what's selected. Since it's callback-driven rather than pre-rendered, the sound updates in real time as you move your hands, with no noticeable lag between gesture and audio.

I also smoothed the raw landmark coordinates before feeding them into the pitch/volume calculations. Without that, the pitch would jitter around annoyingly because MediaPipe's frame-to-frame tracking isn't perfectly stable — a bit of exponential smoothing fixed that.

## Tech stack

- **Python**
- **OpenCV** – webcam capture and frame processing
- **MediaPipe** – hand landmark detection
- **sounddevice** – real-time audio output
- **NumPy** – waveform generation and math

## Setup

Clone the repo and get a virtual environment going:

```bash
git clone https://github.com/visheshjainn16/hand-gesture-music-synthesizer.git
cd gesture-synth
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

Then just run it:

```bash
python hand_tracking.py
```

Give it a second to open your webcam, then hold up a hand in frame. Press `q` to quit.

There's also a `webcam_test.py` in here — a barebones script I used early on just to check the camera was working before adding any of the hand-tracking logic on top. Worth running first if you're troubleshooting camera access issues on your own machine.

## Controls, quick reference

| Gesture | Effect |
|---|---|
| Move hand up/down | Changes pitch (higher on screen = higher note) |
| Pinch thumb + index closer/further | Changes volume |
| Hold up 1–5 fingers | Switches instrument tone |
| Use both hands | Plays two notes at once |

## Notes / things I'd improve next

- Right now the note range is fixed to two octaves (C4 to C6) — could make that configurable
- No MIDI export yet, so nothing you play gets saved anywhere
- Instrument tones are synthesized waveforms rather than sampled real instruments, so it has more of a retro synth sound than a "real" instrument sound — that's a deliberate simplicity trade-off, not a bug

## Requirements

See `requirements.txt` for exact versions. MediaPipe is pinned to `0.10.9` specifically, since newer versions had some breaking changes with the hand-tracking API I was using.