# Healthcare Chatbot - Complete Build Script
# This script sets up the entire project including backend, frontend, and database

param(
    [switch]$SkipFrontend,
    [switch]$SkipBackend,
    [switch]$SkipPrisma,
    [switch]$SkipRAGIndex,
    [string]$PythonVersion = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Healthcare Chatbot - Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$prerequisitesMet = $true

# Detect Python command
$pythonCmd = $null
if (Test-Command "python") {
    $pythonCmd = "python"
} elseif (Test-Command "python3") {
    $pythonCmd = "python3"
} elseif (Test-Command "py") {
    $pythonCmd = "py"
} else {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    $prerequisitesMet = $false
}

if ($pythonCmd) {
    $pythonVersion = & $pythonCmd --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
    $PythonVersion = $pythonCmd  # Update the variable for later use
}

if (-not $SkipFrontend) {
    if (-not (Test-Command "node")) {
        Write-Host "❌ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
        $prerequisitesMet = $false
    } else {
        $nodeVersion = node --version
        Write-Host "✅ Found: Node.js $nodeVersion" -ForegroundColor Green
    }

    if (-not (Test-Command "npm") -and -not (Test-Command "pnpm")) {
        Write-Host "❌ npm or pnpm not found. Please install npm or pnpm" -ForegroundColor Red
        $prerequisitesMet = $false
    } else {
        if (Test-Command "pnpm") {
            $packageManager = "pnpm"
            $packageVersion = pnpm --version
            Write-Host "✅ Found: pnpm $packageVersion" -ForegroundColor Green
        } else {
            $packageManager = "npm"
            $packageVersion = npm --version
            Write-Host "✅ Found: npm $packageVersion" -ForegroundColor Green
        }
    }
}

if (-not $prerequisitesMet) {
    Write-Host ""
    Write-Host "Please install missing prerequisites and run the script again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "All prerequisites met!" -ForegroundColor Green
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# ============================================
# Backend Setup
# ============================================
if (-not $SkipBackend) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setting up Backend (Python/FastAPI)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $apiDir = Join-Path $scriptDir "api"
    
    if (-not (Test-Path $apiDir)) {
        Write-Host "❌ API directory not found: $apiDir" -ForegroundColor Red
        exit 1
    }

    Set-Location $apiDir

    # Create virtual environment if it doesn't exist
    $venvPath = Join-Path $apiDir ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
        & $PythonVersion -m venv .venv
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "✅ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not activate virtual environment. Continuing..." -ForegroundColor Yellow
    }

    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $PythonVersion -m pip install --upgrade pip --quiet
    Write-Host "✅ pip upgraded" -ForegroundColor Green

    # Install Python dependencies
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    if (Test-Path "requirements.txt") {
        & $PythonVersion -m pip install -r requirements.txt
        Write-Host "✅ Python dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  requirements.txt not found. Skipping..." -ForegroundColor Yellow
    }

    # Check for .env file
    $envFile = Join-Path $apiDir ".env"
    if (-not (Test-Path $envFile)) {
        Write-Host ""
        Write-Host "⚠️  .env file not found in api/ directory" -ForegroundColor Yellow
        Write-Host "Creating template .env file..." -ForegroundColor Yellow
        
        $envTemplate = @"
# Database Configuration
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# ElevenLabs Configuration (optional, for TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# ChromaDB Configuration
CHROMADB_DISABLE_TELEMETRY=1

# JWT Configuration
JWT_SECRET_KEY=your_secret_key_here_change_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
"@
        Set-Content -Path $envFile -Value $envTemplate
        Write-Host "✅ Template .env file created. Please update it with your actual values." -ForegroundColor Green
    } else {
        Write-Host "✅ .env file found" -ForegroundColor Green
    }

    Write-Host ""
}

# ============================================
# Prisma Setup
# ============================================
if (-not $SkipPrisma) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setting up Prisma Database" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $apiDir = Join-Path $scriptDir "api"
    Set-Location $apiDir

    # Check if Prisma is installed
    Write-Host "Checking Prisma installation..." -ForegroundColor Yellow
    try {
        $prismaVersion = & $PythonVersion -m prisma --version 2>&1
        Write-Host "✅ Prisma is installed" -ForegroundColor Green
    } catch {
        Write-Host "Installing Prisma..." -ForegroundColor Yellow
        & $PythonVersion -m pip install prisma
        Write-Host "✅ Prisma installed" -ForegroundColor Green
    }

    # Check for Prisma schema
    $schemaPath = Join-Path $apiDir "prisma\schema.prisma"
    if (-not (Test-Path $schemaPath)) {
        Write-Host "❌ Prisma schema not found: $schemaPath" -ForegroundColor Red
        Write-Host "Skipping Prisma setup..." -ForegroundColor Yellow
    } else {
        # Check for NEON_DB_URL in environment
        $envContent = Get-Content $envFile -ErrorAction SilentlyContinue
        $hasDbUrl = $envContent | Where-Object { $_ -match "NEON_DB_URL" -and $_ -notmatch "^#" -and $_ -notmatch "^\s*$" }
        
        if (-not $hasDbUrl) {
            Write-Host "⚠️  NEON_DB_URL not found in .env file" -ForegroundColor Yellow
            Write-Host "Skipping Prisma database push. Please set NEON_DB_URL in .env file first." -ForegroundColor Yellow
        } else {
            # Generate Prisma client
            Write-Host "Generating Prisma client..." -ForegroundColor Yellow
            try {
                & $PythonVersion -m prisma generate --schema prisma/schema.prisma
                Write-Host "✅ Prisma client generated" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  Error generating Prisma client: $_" -ForegroundColor Yellow
                Write-Host "You may need to run this manually: python -m prisma generate --schema prisma/schema.prisma" -ForegroundColor Yellow
            }

            # Push schema to database
            Write-Host "Pushing schema to database..." -ForegroundColor Yellow
            Write-Host "⚠️  This will create/modify database tables. Continue? (Y/N)" -ForegroundColor Yellow
            $response = Read-Host
            if ($response -eq "Y" -or $response -eq "y") {
                try {
                    & $PythonVersion -m prisma db push --schema prisma/schema.prisma --accept-data-loss
                    Write-Host "✅ Database schema pushed successfully" -ForegroundColor Green
                } catch {
                    Write-Host "⚠️  Error pushing schema: $_" -ForegroundColor Yellow
                    Write-Host "You may need to run this manually: python -m prisma db push --schema prisma/schema.prisma" -ForegroundColor Yellow
                }
            } else {
                Write-Host "Skipping database push. You can run it later with:" -ForegroundColor Yellow
                Write-Host "  python -m prisma db push --schema prisma/schema.prisma" -ForegroundColor Yellow
            }
        }
    }

    Write-Host ""
}

# ============================================
# RAG Index Build
# ============================================
if (-not $SkipRAGIndex) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Building RAG Index" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $apiDir = Join-Path $scriptDir "api"
    Set-Location $apiDir

    $buildIndexScript = Join-Path $apiDir "rag\build_index.py"
    if (Test-Path $buildIndexScript) {
        Write-Host "Building RAG index from markdown files..." -ForegroundColor Yellow
        try {
            & $PythonVersion rag\build_index.py
            Write-Host "✅ RAG index built successfully" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Error building RAG index: $_" -ForegroundColor Yellow
            Write-Host "You can run this manually later: python rag/build_index.py" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  RAG build script not found: $buildIndexScript" -ForegroundColor Yellow
        Write-Host "Skipping RAG index build..." -ForegroundColor Yellow
    }

    Write-Host ""
}

# ============================================
# Frontend Setup
# ============================================
if (-not $SkipFrontend) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Setting up Frontend (Next.js)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $frontendDir = Join-Path $scriptDir "frontend"
    
    if (-not (Test-Path $frontendDir)) {
        Write-Host "❌ Frontend directory not found: $frontendDir" -ForegroundColor Red
        Write-Host "Skipping frontend setup..." -ForegroundColor Yellow
    } else {
        Set-Location $frontendDir

        # Install dependencies
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        if ($packageManager -eq "pnpm") {
            if (-not (Test-Path "node_modules")) {
                pnpm install
                Write-Host "✅ Frontend dependencies installed (pnpm)" -ForegroundColor Green
            } else {
                Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
            }
        } else {
            if (-not (Test-Path "node_modules")) {
                npm install
                Write-Host "✅ Frontend dependencies installed (npm)" -ForegroundColor Green
            } else {
                Write-Host "✅ Frontend dependencies already installed" -ForegroundColor Green
            }
        }

        # Build frontend
        Write-Host "Building frontend..." -ForegroundColor Yellow
        try {
            if ($packageManager -eq "pnpm") {
                pnpm run build
            } else {
                npm run build
            }
            Write-Host "✅ Frontend built successfully" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Error building frontend: $_" -ForegroundColor Yellow
            Write-Host "You can build it manually later with: npm run build (or pnpm run build)" -ForegroundColor Yellow
        }

        Write-Host ""
    }
}

# ============================================
# Summary
# ============================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update api/.env file with your actual configuration values" -ForegroundColor White
Write-Host "2. Start the backend server:" -ForegroundColor White
Write-Host "   cd api" -ForegroundColor Gray
Write-Host "   python start_server.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the frontend (in a new terminal):" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
if ($packageManager -eq "pnpm") {
    Write-Host "   pnpm dev" -ForegroundColor Gray
} else {
    Write-Host "   npm run dev" -ForegroundColor Gray
}
Write-Host ""

Write-Host "For more information, check the documentation in the api/ directory." -ForegroundColor Cyan
Write-Host ""

