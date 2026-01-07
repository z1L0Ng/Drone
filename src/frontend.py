import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt


# =========================
# Fixed inputs (as requested)
# =========================
NOISE_WAV = "/files1/Zilong/Drone/dataset/raw/tellonoise/19700101_000018.wav"
CMD_WAV   = "/files1/Zilong/Drone/dataset/raw/emergency/stop/0a2b400e_nohash_4.wav"

SR = 16000
DURATION_SEC = 1.0
SNR_DB = -30.0

# Feature params (keep consistent with your pipeline if needed)
N_FFT = 1024
HOP = 256
N_MELS = 64
FMIN = 50
FMAX = None  # or SR//2

OUTDIR = "/files1/Zilong/Drone/frontend_test_out_snr_-30"


def rms(x: np.ndarray, eps: float = 1e-12) -> float:
    return float(np.sqrt(np.mean(x * x) + eps))


def load_1s_mono(path: str, sr: int, length: int) -> np.ndarray:
    y, _ = librosa.load(path, sr=sr, mono=True)
    if len(y) < length:
        y = np.pad(y, (0, length - len(y)))
    else:
        y = y[:length]
    return y


def mix_with_snr(clean: np.ndarray, noise: np.ndarray, snr_db: float, eps: float = 1e-12):
    """
    mixture = clean + noise_scaled s.t. SNR(clean, noise_scaled) = snr_db
    """
    rc = rms(clean, eps)
    rn = rms(noise, eps)
    if rn < eps:
        raise ValueError("Noise RMS too small (noise is nearly silent).")

    scale = rc / (rn * (10 ** (snr_db / 20.0)))
    noise_scaled = noise * scale
    mixture = clean + noise_scaled
    return mixture, noise_scaled


def stft(y, n_fft=1024, hop_length=256):
    return librosa.stft(y, n_fft=n_fft, hop_length=hop_length)


def istft(D, hop_length=256, length=None):
    return librosa.istft(D, hop_length=hop_length, length=length)


def wiener_denoise_with_noise_ref(
    y_mix: np.ndarray,
    y_noise_ref: np.ndarray,
    n_fft: int = 1024,
    hop_length: int = 256,
    eps: float = 1e-12,
):
    """
    Wiener filter using known noise reference.
    Ps = max(Px - Pn, 0)
    G  = Ps / (Ps + Pn)
    """
    X = stft(y_mix, n_fft=n_fft, hop_length=hop_length)
    N = stft(y_noise_ref, n_fft=n_fft, hop_length=hop_length)

    Px = np.abs(X) ** 2
    Pn = np.abs(N) ** 2

    T = min(Px.shape[1], Pn.shape[1])
    Px, Pn, X = Px[:, :T], Pn[:, :T], X[:, :T]

    Ps = np.maximum(Px - Pn, 0.0)
    G = Ps / (Ps + Pn + eps)

    Y = G * X
    y_out = istft(Y, hop_length=hop_length, length=len(y_mix))
    return y_out, G


def mel_power(y, sr, n_fft, hop_length, n_mels, fmin=50, fmax=None):
    return librosa.feature.melspectrogram(
        y=y,
        sr=sr,
        n_fft=n_fft,
        hop_length=hop_length,
        n_mels=n_mels,
        fmin=fmin,
        fmax=fmax,
        power=2.0,
    )


def logmel(mel_pwr, top_db=80.0):
    return librosa.power_to_db(mel_pwr, ref=np.max, top_db=top_db)


def pcen(mel_pwr, sr, hop_length):
    # Good starting defaults for noisy far-field / mechanical noise
    return librosa.pcen(
        mel_pwr,
        sr=sr,
        hop_length=hop_length,
        gain=0.98,
        bias=2.0,
        power=0.5,
        time_constant=0.06,
        eps=1e-6,
    )


def save_spec(S, out_path, title, sr, hop_length):
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(S, x_axis="time", y_axis="mel", sr=sr, hop_length=hop_length)
    plt.title(title)
    plt.colorbar()
    plt.tight_layout()
    plt.savefig(out_path, dpi=170)
    plt.close()


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    L = int(SR * DURATION_SEC)

    y_cmd = load_1s_mono(CMD_WAV, SR, L)
    y_noise = load_1s_mono(NOISE_WAV, SR, L)

    y_mix, y_noise_scaled = mix_with_snr(y_cmd, y_noise, SNR_DB)

    y_wiener, G = wiener_denoise_with_noise_ref(
        y_mix, y_noise_scaled, n_fft=N_FFT, hop_length=HOP
    )

    # ===== raw mix features =====
    mel_mix = mel_power(y_mix, SR, N_FFT, HOP, N_MELS, FMIN, FMAX)
    logmel_mix = logmel(mel_mix)
    pcen_mix = pcen(mel_mix, SR, HOP)

    # ===== wiener enhanced features =====
    mel_w = mel_power(y_wiener, SR, N_FFT, HOP, N_MELS, FMIN, FMAX)
    logmel_w = logmel(mel_w)
    pcen_w = pcen(mel_w, SR, HOP)

    save_spec(logmel_mix, os.path.join(OUTDIR, "1_logmel_mix.png"),
              f"Log-Mel (mix) SNR={SNR_DB} dB", SR, HOP)
    save_spec(pcen_mix, os.path.join(OUTDIR, "2_pcen_mix.png"),
              f"PCEN (mix) SNR={SNR_DB} dB", SR, HOP)
    save_spec(logmel_w, os.path.join(OUTDIR, "3_logmel_wiener.png"),
              f"Log-Mel (Wiener) SNR={SNR_DB} dB", SR, HOP)
    save_spec(pcen_w, os.path.join(OUTDIR, "4_pcen_wiener.png"),
              f"PCEN (Wiener) SNR={SNR_DB} dB", SR, HOP)

    print("=== Frontend test done ===")
    print("CMD:", CMD_WAV)
    print("NOISE:", NOISE_WAV)
    print("SNR(dB):", SNR_DB)
    print("rms cmd:", rms(y_cmd), "rms noise_scaled:", rms(y_noise_scaled), "rms mix:", rms(y_mix))
    print("shapes: logmel_mix", logmel_mix.shape, "pcen_mix", pcen_mix.shape)
    print("saved images to:", OUTDIR)


if __name__ == "__main__":
    main()