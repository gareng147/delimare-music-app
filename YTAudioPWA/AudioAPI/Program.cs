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

// Fungsi helper untuk menjalankan proses Python (Beranda, Search, Playlist)
Func<string, string, Task<IResult>> runPythonEngine = async (mode, url) =>
{
    if (string.IsNullOrEmpty(url)) return Results.BadRequest(new { error = "URL kosong!" });

    var workingDir = Path.Combine(Directory.GetCurrentDirectory(), "PythonEngine");
    var isWindows = System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows);
    var pythonExe = isWindows 
        ? Path.Combine(workingDir, "env", "Scripts", "python.exe")
        : Path.Combine(workingDir, "env", "bin", "python");

    var scriptPath = Path.Combine(workingDir, "extractor.py");

    var startInfo = new ProcessStartInfo
    {
        FileName = pythonExe,
        Arguments = $"\"{scriptPath}\" \"{mode}\" \"{url}\"",
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

app.MapGet("/api/stream", async (string url) => await runPythonEngine("stream", url));
app.MapGet("/api/playlist", async (string url) => await runPythonEngine("playlist", url));
app.MapGet("/api/search", async (string q) => await runPythonEngine("search", q));
app.MapGet("/api/home", async () => await runPythonEngine("home", "default_feed"));

// Endpoint Proxy Audio (Disamakan jalurnya dengan fungsi runPythonEngine di atas)
app.MapGet("/api/audio-proxy", async (string videoUrl, HttpContext context) =>
{
    try
    {
        if (string.IsNullOrEmpty(videoUrl)) return Results.BadRequest("URL video kosong!");

        var workingDir = Path.Combine(Directory.GetCurrentDirectory(), "PythonEngine");
        var isWindows = System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows);
        var pythonExe = isWindows 
            ? Path.Combine(workingDir, "env", "Scripts", "python.exe")
            : Path.Combine(workingDir, "env", "bin", "python");

        var scriptPath = Path.Combine(workingDir, "extractor.py");

        var psi = new ProcessStartInfo
        {
            FileName = pythonExe,
            Arguments = $"\"{scriptPath}\" \"stream\" \"{videoUrl}\"",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = workingDir
        };

        using var process = Process.Start(psi);
        if (process == null) return Results.Problem("Gagal menjalankan engine Python.");

        string pythonOutput = await process.StandardOutput.ReadToEndAsync();
        await process.WaitForExitAsync();

        var json = JsonDocument.Parse(pythonOutput);
        if (!json.RootElement.GetProperty("success").GetBoolean())
        {
            return Results.BadRequest("Gagal mengekstrak audio dari YouTube");
        }

        string realStreamUrl = json.RootElement.GetProperty("stream_url").GetString();

        using var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.UserAgent.ParseAdd("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36");

        var requestMessage = new HttpRequestMessage(HttpMethod.Get, realStreamUrl);
        if (context.Request.Headers.TryGetValue("Range", out var rangeHeader))
        {
            requestMessage.Headers.TryAddWithoutValidation("Range", rangeHeader.ToString());
        }

        var response = await httpClient.SendAsync(requestMessage, HttpCompletionOption.ResponseHeadersRead);
        
        if (!response.IsSuccessStatusCode)
        {
            return Results.Problem($"YouTube menolak akses direct stream: {(int)response.StatusCode}");
        }

        var stream = await response.Content.ReadAsStreamAsync();
        var contentType = response.Content.Headers.ContentType?.MediaType ?? "audio/mp4";

        return Results.Stream(stream, contentType, enableRangeProcessing: true);
    }
    catch (Exception ex)
    {
        return Results.BadRequest($"Proxy Error: {ex.Message}");
    }
});

app.Run("http://0.0.0.0:5000");