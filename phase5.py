import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# --- Page config ---
st.set_page_config(page_title="EW Scan Simulator", layout="wide", page_icon="📡")

st.title("📡 Smart Scan Strategy — EW Simulation")
st.markdown("Simulate Electronic Warfare frequency spectrum scanning and compare strategies.")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Simulation Controls")

strategy = st.sidebar.selectbox(
    "Select Scan Strategy",
    ["Linear", "Random", "Adaptive"]
)

n_samples = st.sidebar.slider("Random/Adaptive Initial Samples", 50, 500, 200)
threshold = st.sidebar.slider("Threat Threshold (dBm)", -85, -50, -70)

run = st.sidebar.button("🚀 Run Simulation")

# --- Spectrum setup ---
FREQ_MIN = 100
FREQ_MAX = 6000
RESOLUTION = 1000

frequencies = np.linspace(FREQ_MIN, FREQ_MAX, RESOLUTION)

def inject_signal(spectrum, freq_array, center_freq, power_dbm, bandwidth=20):
    signal = power_dbm * np.exp(-((freq_array - center_freq) ** 2) / (2 * bandwidth ** 2))
    return spectrum + signal

def generate_spectrum():
    noise_floor = np.random.normal(loc=-90, scale=2, size=RESOLUTION)
    threats = [
        {"freq": 1200, "power": 40, "bw": 30},
        {"freq": 3500, "power": 55, "bw": 15},
        {"freq": 5100, "power": 35, "bw": 50},
    ]
    spectrum = noise_floor.copy()
    for t in threats:
        spectrum = inject_signal(spectrum, frequencies, t["freq"], t["power"], t["bw"])
    return spectrum

def classify_threat(power):
    if power > -50:
        return "🔴 HIGH"
    elif power > -60:
        return "🟠 MEDIUM"
    else:
        return "🟡 LOW"

# --- Scan strategies ---
def linear_scan(spectrum, threshold):
    start = time.perf_counter()
    detections = []
    for i in range(len(spectrum)):
        if spectrum[i] > threshold:
            detections.append((frequencies[i], spectrum[i]))
    end = time.perf_counter()
    return detections, round((end - start) * 1000, 4), len(spectrum)

def random_scan(spectrum, threshold, n_samples):
    start = time.perf_counter()
    detections = []
    indices = np.random.choice(len(spectrum), size=n_samples, replace=False)
    for i in indices:
        if spectrum[i] > threshold:
            detections.append((frequencies[i], spectrum[i]))
    end = time.perf_counter()
    return detections, round((end - start) * 1000, 4), n_samples

def adaptive_scan(spectrum, threshold, initial_samples):
    start = time.perf_counter()
    detections = []
    indices = np.random.choice(len(spectrum), size=initial_samples, replace=False)
    hot_zones = []
    scans = initial_samples
    for i in indices:
        if spectrum[i] > threshold:
            detections.append((frequencies[i], spectrum[i]))
            hot_zones.append(i)
    for hz in hot_zones:
        neighborhood = range(max(0, hz - 30), min(len(spectrum), hz + 30))
        for i in neighborhood:
            scans += 1
            if spectrum[i] > threshold:
                entry = (frequencies[i], spectrum[i])
                if entry not in detections:
                    detections.append(entry)
    end = time.perf_counter()
    return detections, round((end - start) * 1000, 4), scans

# --- Main app ---
if run:
    spectrum = generate_spectrum()

    if strategy == "Linear":
        detections, time_ms, scans = linear_scan(spectrum, threshold)
    elif strategy == "Random":
        detections, time_ms, scans = random_scan(spectrum, threshold, n_samples)
    else:
        detections, time_ms, scans = adaptive_scan(spectrum, threshold, n_samples)

    # --- Metrics row ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Strategy", strategy)
    col2.metric("Detections", len(detections))
    col3.metric("Frequencies Scanned", scans)
    col4.metric("Time (ms)", time_ms)

    st.markdown("---")

    # --- Spectrum plot ---
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(frequencies, spectrum, color='cyan', linewidth=0.8, label="Spectrum")
    ax.axhline(y=threshold, color='red', linestyle='--', linewidth=1, label=f"Threshold ({threshold} dBm)")

    if detections:
        det_freqs = [d[0] for d in detections]
        det_powers = [d[1] for d in detections]
        ax.scatter(det_freqs, det_powers, color='orange', s=15, zorder=5, label="Detected")

    ax.set_facecolor('#0a0a0a')
    fig.patch.set_facecolor('#0a0a0a')
    ax.set_title(f"{strategy} Scan — Spectrum View", color='white')
    ax.set_xlabel("Frequency (MHz)", color='white')
    ax.set_ylabel("Power (dBm)", color='white')
    ax.tick_params(colors='white')
    ax.legend()
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)

    st.markdown("---")

    # --- Threat table ---
    st.subheader("🎯 Threat Detection Report")

    if detections:
        threat_data = []
        seen = []
        for d in detections:
            freq, power = d
            already = any(abs(freq - s) < 100 for s in seen)
            if not already:
                seen.append(freq)
                threat_data.append({
                    "Frequency (MHz)": round(freq, 2),
                    "Power (dBm)": round(power, 2),
                    "Severity": classify_threat(power)
                })

        st.table(threat_data)
    else:
        st.warning("No threats detected with current settings.")

    # --- All strategies comparison ---
    st.markdown("---")
    st.subheader("📊 All Strategies Comparison")

    spectrum2 = generate_spectrum()
    l_det, l_time, l_scans = linear_scan(spectrum2, threshold)
    r_det, r_time, r_scans = random_scan(spectrum2, threshold, n_samples)
    a_det, a_time, a_scans = adaptive_scan(spectrum2, threshold, n_samples)

    fig2, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig2.patch.set_facecolor('#0a0a0a')

    metrics = {
        'Detections': [len(l_det), len(r_det), len(a_det)],
        'Scans': [l_scans, r_scans, a_scans],
        'Efficiency %': [
            round(len(l_det)/l_scans*100, 2),
            round(len(r_det)/r_scans*100, 2),
            round(len(a_det)/a_scans*100, 2)
        ]
    }

    for ax, (title, values) in zip(axes, metrics.items()):
        ax.bar(['Linear', 'Random', 'Adaptive'], values, color=['cyan', 'lime', 'orange'])
        ax.set_title(title, color='white')
        ax.set_facecolor('#0a0a0a')
        ax.tick_params(colors='white')

    st.pyplot(fig2)

else:
    st.info("👈 Configure settings in the sidebar and click **Run Simulation** to start.")

st.markdown("""
<style>
.viewerBadge_container__r5tak {display: none;}
.viewerBadge_link__qRIco {display: none;}
</style>
""", unsafe_allow_html=True)
