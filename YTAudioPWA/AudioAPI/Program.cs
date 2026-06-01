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
app.MapGet("/api/audio-proxy", async (string videoUrl) =>
{
    try
    {
        var psi = new System.Diagnostics.ProcessStartInfo
        {
            FileName = "python3",
            Arguments = $"extractor.py stream \"{videoUrl}\"",
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = System.Diagnostics.Process.Start(psi);
        string pythonOutput = await process.StandardOutput.ReadToEndAsync();
        await process.WaitForExitAsync();

        var json = System.Text.Json.JsonDocument.Parse(pythonOutput);
        if (!json.RootElement.GetProperty("success").GetBoolean())
        {
            return Results.BadRequest("Gagal mengekstrak audio dari proxy");
        }

        string realStreamUrl = json.RootElement.GetProperty("stream_url").GetString();
        
        // JALUR KILAT: Alihkan browser langsung ke CDN HTTPS Invidious yang aman dan mendukung buffering penuh
        return Results.Redirect(realStreamUrl);
    }
    catch (Exception ex)
    {
        return Results.BadRequest(ex.Message);
    }
});

// Ubah dari app.Run(); menjadi seperti ini:
app.Run("http://0.0.0.0:5000");