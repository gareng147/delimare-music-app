// Gunakan IP AWS kamu yang abadi (tanpa terowongan lagi)
const BASE_API = ""; // Sesuaikan Port Backend C# Anda

let trackQueue = [];
let currentIndex = -1;

const audioPlayer = document.getElementById('audioPlayer');
const statusDiv = document.getElementById('status');
const homeSection = document.getElementById('homeSection');
const homeGrid = document.getElementById('homeGrid');
const containerResult = document.getElementById('containerResult');
const listTitle = document.getElementById('listTitle');
const listView = document.getElementById('listView');

// 1. OTOMATIS LOAD BERANDA SAAT WEBSITE DIBUKA
window.addEventListener('DOMContentLoaded', loadHomepage);

async function loadHomepage() {
    try {
        const res = await fetch(`${BASE_API}/api/home`);
        const data = await res.json();
        
        if (data.success && data.tracks.length > 0) {
            statusDiv.innerText = "Selamat Datang di Delimare Music!";
            homeGrid.innerHTML = "";
            
            data.tracks.forEach((track) => {
                const card = document.createElement('div');
                card.className = "music-card";
                card.innerHTML = `
                    <img src="${track.thumbnail}" alt="cover">
                    <p>${track.title}</p>
                `;
                // Jika kartu lagu diklik, jadikan dia single track tunggal dan putar!
                card.addEventListener('click', () => {
                    homeSection.style.display = "none";
                    containerResult.style.display = "block";
                    listTitle.innerText = "Memutar Dari Beranda";
                    
                    trackQueue = [{ title: track.title, url: track.url }];
                    currentIndex = 0;
                    renderListView();
                    playTrack();
                });
                homeGrid.appendChild(card);
            });
        } else {
            statusDiv.innerText = "Gagal memuat konten beranda.";
        }
    } catch {
        statusDiv.innerText = "Gagal terhubung ke server backend.";
    }
}

// 2. LOGIKA SEARCH & PLAYLIST
document.getElementById('searchBtn').addEventListener('click', async () => {
    const input = document.getElementById('queryInput').value.trim();
    if (!input) return alert('Masukkan kata kunci atau link!');

    statusDiv.innerText = "Memproses...";
    homeSection.style.display = "none";
    containerResult.style.display = "none";
    trackQueue = [];
    currentIndex = -1;

    if (input.includes("http://") || input.includes("https://")) {
        if (input.includes("list=")) {
            statusDiv.innerText = "Membongkar isi playlist...";
            try {
                const res = await fetch(`${BASE_API}/api/playlist?url=${encodeURIComponent(input)}`);
                const data = await res.json();
                if (data.success && data.tracks.length > 0) {
                    trackQueue = data.tracks;
                    currentIndex = 0;
                    listTitle.innerText = "Daftar Playlist";
                    containerResult.style.display = "block";
                    renderListView();
                    playTrack();
                }
            } catch { statusDiv.innerText = "Gagal memuat playlist."; }
        } else {
            trackQueue = [{ title: "Single Track", url: input }];
            currentIndex = 0;
            containerResult.style.display = "block";
            listTitle.innerText = "Memutar Musik Tunggal";
            renderListView();
            playTrack();
        }
    } else {
        statusDiv.innerText = `Mencari "${input}"...`;
        try {
            const res = await fetch(`${BASE_API}/api/search?q=${encodeURIComponent(input)}`);
            const data = await res.json();
            if (data.success && data.tracks.length > 0) {
                trackQueue = data.tracks;
                listTitle.innerText = `Hasil Pencarian: "${input}"`;
                containerResult.style.display = "block";
                statusDiv.innerText = "Pilih musik untuk diputar.";
                renderListView();
            } else { statusDiv.innerText = "Musik tidak ditemukan."; }
        } catch { statusDiv.innerText = "Server pencarian eror."; }
    }
});

// 3. LOGIKA INTI PEMUTARAN & AUTOPLAY REKOMENDASI PINTAR
async function playTrack() {
    if (currentIndex < 0 || currentIndex >= trackQueue.length) return;

    const track = trackQueue[currentIndex];
    statusDiv.innerText = `Mengambil stream: ${track.title}...`;
    updateHighlight();

    try {
        const res = await fetch(`${BASE_API}/api/stream?url=${encodeURIComponent(track.url)}`);
        const data = await res.json();

        if (data.success) {
            statusDiv.innerHTML = `<strong>Memutar:</strong> ${data.title}`;
            audioPlayer.src = data.stream_url;
            audioPlayer.play();

            // KUNCI UTAMA: Jika ini adalah lagu tunggal (atau lagu terakhir di list pencarian), 
            // Ambil "related_videos" dari Python dan suntikkan ke antrean selanjutnya!
            if (currentIndex === trackQueue.length - 1 && data.related_videos && data.related_videos.length > 0) {
                trackQueue = trackQueue.concat(data.related_videos);
                renderListView(); // Perbarui daftar di bawah agar user melihat rekomendasi berikutnya
            }
        } else {
            statusDiv.innerText = "Gagal memutar lagu ini.";
        }
    } catch { statusDiv.innerText = "Eror koneksi stream."; }
}

function renderListView() {
    listView.innerHTML = "";
    trackQueue.forEach((track, index) => {
        const div = document.createElement('div');
        div.className = "track-item";
        div.id = `track-${index}`;
        div.innerHTML = `<span>${index + 1}. ${track.title}</span> <span>▶</span>`;
        div.addEventListener('click', () => {
            currentIndex = index;
            playTrack();
        });
        listView.appendChild(div);
    });
}

function updateHighlight() {
    document.querySelectorAll('.track-item').forEach(el => el.classList.remove('active'));
    const currentEl = document.getElementById(`track-${currentIndex}`);
    if (currentEl) currentEl.classList.add('active');
}

// AMBIL ELEMEN BARU
const playPauseBtn = document.getElementById('playPauseBtn');
const rewindBtn = document.getElementById('rewindBtn');
const forwardBtn = document.getElementById('forwardBtn');
const seekSlider = document.getElementById('seekSlider');
const volumeSlider = document.getElementById('volumeSlider');
const currentTimeText = document.getElementById('currentTime');
const durationText = document.getElementById('duration');

// 1. FUNGSI MAJU & MUNDUR (SEEKING)
rewindBtn.addEventListener('click', () => {
    audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 10);
});

forwardBtn.addEventListener('click', () => {
    audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 10);
});

// 2. FUNGSI VOLUME (CUSTOM)
volumeSlider.addEventListener('input', (e) => {
    audioPlayer.volume = e.target.value;
});

// 3. UPDATE PROGRESS SLIDER & TEXT SAAT LAGU JALAN
audioPlayer.addEventListener('timeupdate', () => {
    const current = audioPlayer.currentTime;
    const duration = audioPlayer.duration;
    
    if (!isNaN(duration)) {
        seekSlider.value = (current / duration) * 100;
        currentTimeText.innerText = formatTime(current);
        durationText.innerText = formatTime(duration);
    }
});

// 4. BIAR USER BISA KLIK DI TENGAH DURASI UNTUK LOMPAT
seekSlider.addEventListener('input', (e) => {
    const seekTo = (e.target.value / 100) * audioPlayer.duration;
    audioPlayer.currentTime = seekTo;
});

// 5. TOMBOL PLAY/PAUSE MANUAL
playPauseBtn.addEventListener('click', () => {
    if (audioPlayer.paused) {
        audioPlayer.play();
        playPauseBtn.innerText = "⏸";
    } else {
        audioPlayer.pause();
        playPauseBtn.innerText = "▶";
    }
});

// Helper untuk format detik ke menit:detik
function formatTime(seconds) {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec < 10 ? '0' : ''}${sec}`;
}
// Navigasi Umum tombol kontrol
audioPlayer.addEventListener('ended', () => { if (currentIndex < trackQueue.length - 1) document.getElementById('nextBtn').click(); });
document.getElementById('nextBtn').addEventListener('click', () => { if (currentIndex < trackQueue.length - 1) { currentIndex++; playTrack(); } });
document.getElementById('prevBtn').addEventListener('click', () => { if (currentIndex > 0) { currentIndex--; playTrack(); } });