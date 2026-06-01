using System.Diagnostics;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});

var app = builder.Build();
app.UseCors();

// Fungsi helper untuk menjalankan proses Python
Func<string, string, Task<IResult>> runPythonEngine = async (mode, url) =>
{
    if (string.IsNullOrEmpty(url)) return Results.BadRequest(new { error = "URL kosong!" });

    var workingDir = Path.Combine(Directory.GetCurrentDirectory(), "PythonEngine");
    
    // PERBAIKAN: Deteksi otomatis apakah server menggunakan Windows atau Linux
    var isWindows = System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows);
    var pythonExe = isWindows 
        ? Path.Combine(workingDir, "env", "Scripts", "python.exe")
        : Path.Combine(workingDir, "env", "bin", "python"); // Jalur untuk Linux Server

    var scriptPath = Path.Combine(workingDir, "extractor.py");

    // PERBAIKAN: Pastikan scriptPath dimasukkan sebagai argumen pertama Python
    var startInfo = new ProcessStartInfo
    {
        FileName = pythonExe,
        Arguments = $"\"{scriptPath}\" \"{mode}\" \"{url}\"", // <-- Bagian ini sudah diperbaiki
        RedirectStandardOutput = true,
        RedirectStandardError = true,
        UseShellExecute = false,
        CreateNoWindow = true,
        WorkingDirectory = workingDir
    };

    try
    {
        using var process = Process.Start(startInfo);
        if (process == null) return Results.Problem("Gagal menjalankan engine.");

        string output = await process.StandardOutput.ReadToEndAsync();
        await process.WaitForExitAsync();

        var jsonResult = JsonDocument.Parse(output);
        return Results.Ok(jsonResult.RootElement);
    }
    catch (Exception ex)
    {
        return Results.Problem($"Error: {ex.Message}");
    }
};

// Endpoint 1: Mengambil stream audio satuan
app.MapGet("/api/stream", async (string url) => await runPythonEngine("stream", url));

// Endpoint 2: Mengambil daftar lagu dari playlist/mix
app.MapGet("/api/playlist", async (string url) => await runPythonEngine("playlist", url));

// Endpoint 3: Mencari lagu berdasarkan kata kunci pencarian
app.MapGet("/api/search", async (string q) => await runPythonEngine("search", q));

// Endpoint 4: Mengambil konten musik rekomendasi untuk halaman beranda (Fitur Baru)
app.MapGet("/api/home", async () => await runPythonEngine("home", "default_feed"));

// Endpoint Baru: Proxy Audio untuk Menjebol IP-Lock YouTube
// Endpoint Proxy Audio Versi Upgrade (Anti-Blokir & Mendukung Buffering/Seeking)
app.MapGet("/api/audio-proxy", async (string url, HttpContext context) =>
{
    var httpClient = new HttpClient();
    
    // 1. WAJIB: Palsukan User-Agent agar YouTube mengira ini browser manusia, bukan bot AWS
    httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");

    // 2. Operkan permintaan "Range" dari HP/Browser kamu langsung ke YouTube
    var requestMessage = new HttpRequestMessage(HttpMethod.Get, url);
    if (context.Request.Headers.TryGetValue("Range", out var rangeHeader))
    {
        requestMessage.Headers.TryAddWithoutValidation("Range", rangeHeader.ToString());
    }

    var response = await httpClient.SendAsync(requestMessage, HttpCompletionOption.ResponseHeadersRead);
    var stream = await response.Content.ReadAsStreamAsync();
    var contentType = response.Content.Headers.ContentType?.MediaType ?? "audio/mp4";

    // 3. WAJIB: Aktifkan enableRangeProcessing agar lagu bisa di-skip/forward tanpa macet
    return Results.Stream(stream, contentType, enableRangeProcessing: true);
});

// Ubah dari app.Run(); menjadi seperti ini:
app.Run("http://0.0.0.0:5000");