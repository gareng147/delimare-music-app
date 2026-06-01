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
    var pythonExe = Path.Combine(workingDir, "env", "Scripts", "python.exe");
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

// Ubah dari app.Run(); menjadi seperti ini:
app.Run("http://0.0.0.0:5000");