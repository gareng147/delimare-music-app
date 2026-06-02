FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS base
WORKDIR /app
EXPOSE 8080

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["AudioAPI.csproj", "."]
RUN dotnet restore "./AudioAPI.csproj"
COPY . .
RUN dotnet build "AudioAPI.csproj" -c Release -o /app/build

FROM build AS publish
RUN dotnet publish "AudioAPI.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .

RUN mkdir -p PythonEngine
COPY PythonEngine/extractor.py ./PythonEngine/
COPY PythonEngine/cookies.txt ./PythonEngine/

RUN python3 -m venv PythonEngine/env
RUN ./PythonEngine/env/bin/pip install yt-dlp

# BUKA GEMBOK AKSES FOLDER SECARA PERMANEN
RUN chmod -R 777 /app/PythonEngine

ENTRYPOINT ["dotnet", "AudioAPI.dll"]