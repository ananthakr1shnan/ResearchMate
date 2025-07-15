import os
import sys
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# Import settings and ResearchMate components
from src.components.research_assistant import ResearchMate
from src.components.citation_network import CitationNetworkAnalyzer
from src.components.auth import AuthManager

# Initialize only essential components at startup (fast components only)
auth_manager = AuthManager()
security = HTTPBearer(auto_error=False)

# Simple settings for development
class Settings:
    def __init__(self):
        self.server = type('ServerSettings', (), {
            'debug': False,
            'host': '0.0.0.0',
            'port': int(os.environ.get('PORT', 80))  # Changed default from 8000 to 80 for Azure
        })()
        self.security = type('SecuritySettings', (), {
            'cors_origins': ["*"],
            'cors_methods': ["*"],
            'cors_headers': ["*"]
        })()
    
    def get_static_dir(self):
        return "src/static"
    
    def get_templates_dir(self):
        return "src/templates"

settings = Settings()

# Initialize ResearchMate and Citation Analyzer (will be done during loading screen)
research_mate = None
citation_analyzer = None

# Global initialization flag
research_mate_initialized = False
initialization_in_progress = False

async def initialize_research_mate():
    """Initialize ResearchMate and Citation Analyzer in the background"""
    global research_mate, citation_analyzer, research_mate_initialized, initialization_in_progress
    
    if initialization_in_progress:
        return
    
    initialization_in_progress = True
    print("🚀 Starting ResearchMate background initialization...")
    
    try:
        # Run initialization in thread pool to avoid blocking
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            
            print("📊 Initializing Citation Network Analyzer...")
            citation_analyzer = await loop.run_in_executor(executor, CitationNetworkAnalyzer)
            print("✅ Citation Network Analyzer initialized!")
            
            print("🧠 Initializing ResearchMate core...")
            research_mate = await loop.run_in_executor(executor, ResearchMate)
            print("✅ ResearchMate core initialized!")
        
        research_mate_initialized = True
        print("🎉 All components initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        print("⚠️  Server will start but some features may not work")
        research_mate = None
        citation_analyzer = None
        research_mate_initialized = False
    finally:
        initialization_in_progress = False

# Pydantic models for API
class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")

class QuestionQuery(BaseModel):
    question: str = Field(..., description="Research question")

class ProjectCreate(BaseModel):
    name: str = Field(..., description="Project name")
    research_question: str = Field(..., description="Research question")
    keywords: List[str] = Field(..., description="Keywords")

class ProjectQuery(BaseModel):
    project_id: str = Field(..., description="Project ID")
    question: str = Field(..., description="Question about the project")

class TrendQuery(BaseModel):
    topic: str = Field(..., description="Research topic")

# Authentication models
class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class RegisterRequest(BaseModel):
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")

# Authentication dependency for API endpoints
async def get_current_user_dependency(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    user = None
    
    # Try Authorization header first
    if credentials:
        user = auth_manager.verify_token(credentials.credentials)
    
    # If no user from header, try cookie
    if not user:
        token = request.cookies.get('authToken')
        if token:
            user = auth_manager.verify_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return user

# Authentication for web pages (checks both header and cookie)
async def get_current_user_web(request: Request):
    """Get current user for web page requests (checks both Authorization header and cookies)"""
    user = None
    
    # First try Authorization header
    try:
        credentials = await security(request)
        if credentials:
            user = auth_manager.verify_token(credentials.credentials)
    except:
        pass
    
    # If no user from header, try cookie
    if not user:
        token = request.cookies.get('authToken')
        if token:
            user = auth_manager.verify_token(token)
    
    return user

# Background task to clean up expired sessions
async def cleanup_expired_sessions():
    while True:
        try:
            expired_count = auth_manager.cleanup_expired_sessions()
            if expired_count > 0:
                print(f"Cleaned up {expired_count} expired sessions")
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
        
        # Run cleanup every 30 minutes
        await asyncio.sleep(30 * 60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start ResearchMate initialization in background (non-blocking)
    asyncio.create_task(initialize_research_mate())
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="ResearchMate API",
    description="AI Research Assistant powered by Groq Llama 3.3 70B",
    version="1.0.0",
    debug=settings.server.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=settings.security.cors_methods,
    allow_headers=settings.security.cors_headers,
)

# Mount static files with cache control for development
static_dir = Path(settings.get_static_dir())
static_dir.mkdir(parents=True, exist_ok=True)

# Custom static files class to add no-cache headers for development
class NoCacheStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope):
        response = FileResponse(
            path=full_path, 
            stat_result=stat_result
        )
        # Add no-cache headers for development
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/static", NoCacheStaticFiles(directory=str(static_dir)), name="static")

# Templates
templates_dir = Path(settings.get_templates_dir())
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Loading page route
@app.get("/loading", response_class=HTMLResponse)
async def loading_page(request: Request):
    return templates.TemplateResponse("loading.html", {"request": request})

# Authentication routes
@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    result = auth_manager.create_user(request.username, request.email, request.password)
    if result["success"]:
        return {"success": True, "message": "Account created successfully"}
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    result = auth_manager.authenticate_user(request.username, request.password)
    if result["success"]:
        return {
            "success": True,
            "token": result["token"],
            "user_id": result["user_id"],
            "username": result["username"]
        }
    else:
        raise HTTPException(status_code=401, detail=result["error"])

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Check if ResearchMate is initialized
    global research_mate_initialized
    if not research_mate_initialized:
        return RedirectResponse(url="/loading", status_code=302)
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/api/auth/logout")
async def logout(request: Request):
    # Get current user to invalidate their session
    user = await get_current_user_web(request)
    if user:
        auth_manager.logout_user(user['user_id'])
    
    response = JSONResponse({"success": True, "message": "Logged out successfully"})
    response.delete_cookie("authToken", path="/")
    return response

# Web interface routes (protected)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Check if ResearchMate is initialized first
    global research_mate_initialized
    if not research_mate_initialized:
        return RedirectResponse(url="/loading", status_code=302)
    
    # Check if user is authenticated
    user = await get_current_user_web(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    # Check if ResearchMate is initialized first
    global research_mate_initialized
    if not research_mate_initialized:
        return RedirectResponse(url="/loading", status_code=302)
    
    user = await get_current_user_web(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("search.html", {"request": request, "user": user})

@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    user = await get_current_user_web(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("projects.html", {"request": request, "user": user})

@app.get("/trends", response_class=HTMLResponse)
async def trends_page(request: Request):
    user = await get_current_user_web(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("trends.html", {"request": request, "user": user})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    user = await get_current_user_web(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("upload.html", {"request": request, "user": user})

@app.get("/citation", response_class=HTMLResponse)
async def citation_page(request: Request):
    try:
        if citation_analyzer is None:
            # If citation analyzer isn't initialized yet, show empty state
            summary = {"total_papers": 0, "total_citations": 0, "networks": []}
        else:
            summary = citation_analyzer.get_network_summary()
        return templates.TemplateResponse("citation.html", {"request": request, "summary": summary})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-search", response_class=HTMLResponse)
async def test_search_page(request: Request):
    """Simple test page for debugging search"""
    with open("test_search.html", "r") as f:
        content = f.read()
    return HTMLResponse(content=content)

# Health check endpoint for Azure
@app.get("/health")
async def health_check():
    """Health check endpoint for Azure and other platforms"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# API endpoints
@app.post("/api/search")
async def search_papers(query: SearchQuery, current_user: dict = Depends(get_current_user_dependency)):
    try:
        if research_mate is None:
            raise HTTPException(status_code=503, detail="ResearchMate not initialized")
        rm = research_mate
        result = rm.search(query.query, query.max_results)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Search failed"))
        papers = result.get("papers", [])
        if papers and citation_analyzer is not None:  # Only add papers if citation analyzer is ready
            citation_analyzer.add_papers(papers)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask")
async def ask_question(question: QuestionQuery, current_user: dict = Depends(get_current_user_dependency)):
    try:
        if research_mate is None:
            raise HTTPException(status_code=503, detail="ResearchMate not initialized")
        rm = research_mate
        result = rm.ask(question.question)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Question failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...), current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process PDF
        result = research_mate.upload_pdf(str(file_path))
        
        # Clean up file
        file_path.unlink()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "PDF analysis failed"))
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects")
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        result = research_mate.create_project(project.name, project.research_question, project.keywords, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Project creation failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects(current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        result = research_mate.list_projects(user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to list projects"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        result = research_mate.get_project(project_id, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Project not found"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/search")
async def search_project_literature(project_id: str, max_papers: int = 10, current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        result = research_mate.search_project_literature(project_id, max_papers, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Literature search failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze")
async def analyze_project(project_id: str, current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        result = research_mate.analyze_project(project_id, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Project analysis failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/review")
async def generate_review(project_id: str, current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        result = research_mate.generate_review(project_id, user_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Review generation failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/ask")
async def ask_project_question(project_id: str, question: QuestionQuery):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        result = research_mate.ask_project_question(project_id, question.question)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Project question failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/api/trends")
async def get_trends(trend: TrendQuery):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        result = research_mate.analyze_trends(trend.topic)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("error", "Trend analysis failed"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/temporal")
async def get_temporal_trends(trend: TrendQuery):
    """Get temporal trend analysis"""
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        # Get papers for analysis
        papers = research_mate.search_papers(trend.topic, 50)
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found for temporal analysis")
        
        # Use advanced trend monitor
        result = research_mate.trend_monitor.analyze_temporal_trends(papers)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "topic": trend.topic,
            "temporal_analysis": result,
            "papers_analyzed": len(papers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trends/gaps")
async def detect_research_gaps(trend: TrendQuery):
    """Detect research gaps for a topic"""
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        # Get papers for gap analysis
        papers = research_mate.search_papers(trend.topic, 50)
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found for gap analysis")
        
        # Use advanced trend monitor
        result = research_mate.trend_monitor.detect_research_gaps(papers)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "topic": trend.topic,
            "gap_analysis": result,
            "papers_analyzed": len(papers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status(current_user: dict = Depends(get_current_user_dependency)):
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        result = research_mate.get_status()
        # Ensure proper structure for frontend
        if result.get('success'):
            return {
                'success': True,
                'statistics': result.get('statistics', {
                    'rag_documents': 0,
                    'system_version': '1.0.0',
                    'status_check_time': datetime.now().isoformat()
                }),
                'components': result.get('components', {})
            }
        else:
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialization status endpoint
@app.get("/api/init-status")
async def get_init_status():
    """Check if ResearchMate is initialized"""
    global research_mate_initialized, initialization_in_progress
    
    if research_mate_initialized:
        status = "ready"
    elif initialization_in_progress:
        status = "initializing"
    else:
        status = "not_started"
    
    return {
        "initialized": research_mate_initialized,
        "in_progress": initialization_in_progress,
        "timestamp": datetime.now().isoformat(),
        "status": status
    }

# Fast search endpoint that initializes on first call
@app.post("/api/search-fast")
async def search_papers_fast(query: SearchQuery, current_user: dict = Depends(get_current_user_dependency)):
    """Fast search that shows initialization progress"""
    try:
        global research_mate
        if research_mate is None:
            # Return immediate response indicating initialization
            return {
                "initializing": True,
                "message": "ResearchMate is initializing (this may take 30-60 seconds)...",
                "query": query.query,
                "estimated_time": "30-60 seconds"
            }
        
        # Use existing search
        result = research_mate.search(query.query, query.max_results)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Search failed"))
        
        papers = result.get("papers", [])
        if papers and citation_analyzer is not None:
            citation_analyzer.add_papers(papers)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/status")
async def get_user_status(current_user: dict = Depends(get_current_user_dependency)):
    """Get current user's status and statistics"""
    if research_mate is None:
        raise HTTPException(status_code=503, detail="ResearchMate not initialized")
    
    try:
        user_id = current_user.get("user_id")
        
        # Get user's projects
        projects_result = research_mate.list_projects(user_id)
        if not projects_result.get("success"):
            raise HTTPException(status_code=400, detail="Failed to get user projects")
        
        user_projects = projects_result.get("projects", [])
        total_papers = sum(len(p.get('papers', [])) for p in user_projects)
        
        return {
            "success": True,
            "user_id": user_id,
            "username": current_user.get("username"),
            "statistics": {
                "total_projects": len(user_projects),
                "total_papers": total_papers,
                "active_projects": len([p for p in user_projects if p.get('status') == 'active'])
            },
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Trigger initialization endpoint (for testing)
@app.post("/api/trigger-init")
async def trigger_initialization():
    """Manually trigger ResearchMate initialization"""
    if not initialization_in_progress and not research_mate_initialized:
        asyncio.create_task(initialize_research_mate())
        return {"message": "Initialization triggered"}
    elif initialization_in_progress:
        return {"message": "Initialization already in progress"}
    else:
        return {"message": "Already initialized"}

# Legacy health check endpoint
@app.get("/api/health")
async def api_health_check():
    """Legacy health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Update the existing FastAPI app to use lifespan
app.router.lifespan_context = lifespan

# Startup event to ensure initialization begins immediately after server starts
@app.on_event("startup")
async def startup_event():
    """Ensure initialization starts on startup"""
    print("🌟 Server started, ensuring ResearchMate initialization begins...")
    # Give the server a moment to fully start, then trigger initialization
    await asyncio.sleep(1)
    if not initialization_in_progress and not research_mate_initialized:
        asyncio.create_task(initialize_research_mate())

# Run the application
if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 80))
    host = "0.0.0.0"  # Use 0.0.0.0 to listen on all interfaces

    print(f"Starting ResearchMate on Azure Container Instance...")
    print(f"Web Interface: http://0.0.0.0:{port}")
    print(f"API Documentation: http://0.0.0.0:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info"
    )