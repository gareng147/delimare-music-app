# 1. Gunakan Base Image ASP.NET Runtime resmi dari Microsoft
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

# Instal Python3 dan Pip di dalam lingkungan Linux Server
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*

# 2. Tahap Build Aplikasi C# menggunakan .NET SDK
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["AudioAPI.csproj", "."]
RUN dotnet restore "./AudioAPI.csproj"
COPY . .
RUN dotnet build "AudioAPI.csproj" -c Release -o /app/build

# 3. Tahap Publish Aplikasi
FROM build AS publish
RUN dotnet publish "AudioAPI.csproj" -c Release -o /app/publish /p:UseAppHost=false

# 4. Tahap Akhir: Satukan C# dan Python Virtual Environment
FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .

# Buat otomatis Virtual Environment Python di server dan instal yt-dlp
RUN mkdir -p PythonEngine
COPY PythonEngine/extractor.py ./PythonEngine/
RUN python3 -m venv PythonEngine/env
RUN ./PythonEngine/env/bin/pip install yt-dlp

# Jalankan server API
ENTRYPOINT ["dotnet", "AudioAPI.dll"]