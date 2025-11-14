# audio_vad.py
import librosa
import numpy as np

def get_vad_segments(audio_path, frame_duration=0.04):
    """
    Returns a list of audio features per frame:
    - audio_energy: RMS energy
    - speech_intensity: normalized energy
    - is_talking: True if above threshold
    - speech_prob: probability-like score
    """
    audio, sr = librosa.load(audio_path, sr=None)
    hop_length = int(sr * frame_duration)
    
    # Frame the audio
    if len(audio) < hop_length:
        frames = np.pad(audio, (0, hop_length - len(audio)))
        frames = frames.reshape(1, -1)
    else:
        frames = librosa.util.frame(audio, frame_length=hop_length, hop_length=hop_length).T
    
    rms = np.sqrt(np.mean(frames ** 2, axis=1))  # RMS energy per frame
    energy_threshold = np.percentile(rms, 50)    # median energy as threshold
    
    results = []
    max_rms = np.max(rms) + 1e-9
    for e in rms:
        speech_intensity = float(e / max_rms)      # normalized 0..1
        is_talking = bool(e > energy_threshold)
        speech_prob = float(min(1.0, e / (energy_threshold + 1e-9)))
        results.append({
            "audio_energy": float(e),
            "speech_intensity": speech_intensity,
            "is_talking": is_talking,
            "speech_prob": speech_prob
        })
    return results

