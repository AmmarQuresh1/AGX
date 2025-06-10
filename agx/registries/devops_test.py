"""
devops_test.py

DevOps automation registry for deployment and infrastructure management.
Demo-ready functions for Fly.io, Docker, and cloud operations.
Keep imports inside functions or adjust the compiler.
"""

def log_message(message: str) -> None:
    print(f"[AGX DEVOPS] {message}")

def check_docker_status() -> str:
    """Check if Docker is running and get basic info"""
    import subprocess
    
    try:
        # Check Docker version
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        
        # Get running containers count
        result = subprocess.run(['docker', 'ps', '--format', 'json'], capture_output=True, text=True, check=True)
        containers = len([line for line in result.stdout.strip().split('\n') if line.strip()])
        
        return f"Docker Status: {version}, Running containers: {containers}"
    except subprocess.CalledProcessError as e:
        return f"Docker not available: {e}"
    except FileNotFoundError:
        return "Docker not installed or not in PATH"

def build_docker_image(image_name: str, dockerfile_path: str = ".") -> str:
    """Build a Docker image from Dockerfile"""
    import subprocess
    import time
    
    try:
        log_message(f"Building Docker image: {image_name}")
        start_time = time.time()
        
        result = subprocess.run([
            'docker', 'build', 
            '-t', image_name, 
            dockerfile_path
        ], capture_output=True, text=True, check=True)
        
        build_time = round(time.time() - start_time, 2)
        return f"✅ Image '{image_name}' built successfully in {build_time}s"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Build failed: {e.stderr}"

def deploy_to_fly(app_name: str, region: str = "ord") -> str:
    """Deploy application to Fly.io"""
    import subprocess
    import time
    
    try:
        log_message(f"Deploying {app_name} to Fly.io region {region}")
        start_time = time.time()
        
        # Check if app exists, create if not
        try:
            subprocess.run(['flyctl', 'status', '-a', app_name], 
                         capture_output=True, check=True)
            log_message(f"App {app_name} exists, updating...")
        except subprocess.CalledProcessError:
            log_message(f"Creating new app {app_name}...")
            subprocess.run(['flyctl', 'apps', 'create', app_name, '--region', region], 
                         capture_output=True, check=True)
        
        # Deploy
        result = subprocess.run(['flyctl', 'deploy', '-a', app_name], 
                              capture_output=True, text=True, check=True)
        
        deploy_time = round(time.time() - start_time, 2)
        
        return f"🚀 Deployed {app_name} to Fly.io in {deploy_time}s\n📍 Region: {region}\n🌐 URL: https://{app_name}.fly.dev"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Deployment failed: {e.stderr}"
    except FileNotFoundError:
        return "❌ flyctl not installed. Install with: curl -L https://fly.io/install.sh | sh"

def scale_fly_app(app_name: str, instances: int) -> str:
    """Scale Fly.io application instances"""
    import subprocess
    
    try:
        log_message(f"Scaling {app_name} to {instances} instances")
        
        result = subprocess.run([
            'flyctl', 'scale', 'count', str(instances), 
            '-a', app_name
        ], capture_output=True, text=True, check=True)
        
        return f"📈 Scaled {app_name} to {instances} instances"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Scaling failed: {e.stderr}"

def get_app_status(app_name: str) -> str:
    """Get comprehensive status of deployed application"""
    import subprocess
    import json
    
    try:
        # Fly.io status
        result = subprocess.run(['flyctl', 'status', '-a', app_name, '--json'], 
                              capture_output=True, text=True, check=True)
        status_data = json.loads(result.stdout)
        
        app_status = status_data.get('Status', 'unknown')
        instances = len(status_data.get('Allocations', []))
        
        # Get recent logs
        logs_result = subprocess.run(['flyctl', 'logs', '-a', app_name, '--limit', '5'], 
                                   capture_output=True, text=True, check=True)
        
        return f"""📊 App Status for {app_name}:
Status: {app_status}
Instances: {instances}
URL: https://{app_name}.fly.dev

Recent Logs:
{logs_result.stdout[-200:]}"""
        
    except subprocess.CalledProcessError as e:
        return f"❌ Status check failed: {e.stderr}"
    except json.JSONDecodeError:
        return f"❌ Failed to parse status data"

def create_dockerfile(app_type: str = "node", port: int = 3000) -> str:
    """Generate a Dockerfile for common application types"""
    
    dockerfiles = {
        "node": f"""FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE {port}
CMD ["npm", "start"]""",
        
        "python": f"""FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "app.py"]""",
        
        "go": f"""FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE {port}
CMD ["./main"]"""
    }
    
    dockerfile_content = dockerfiles.get(app_type, dockerfiles["node"])
    
    try:
        with open("Dockerfile", "w") as f:
            f.write(dockerfile_content)
        return f"✅ Created Dockerfile for {app_type} app (port {port})"
    except Exception as e:
        return f"❌ Failed to create Dockerfile: {e}"

def monitor_deployment(app_name: str, duration: int = 60) -> str:
    """Monitor deployment metrics and logs"""
    import subprocess
    import time
    
    try:
        log_message(f"Monitoring {app_name} for {duration} seconds...")
        
        start_time = time.time()
        metrics = []
        
        while time.time() - start_time < duration:
            # Get current status
            result = subprocess.run(['flyctl', 'status', '-a', app_name, '--json'], 
                                  capture_output=True, text=True, check=True)
            
            # Simple health check
            status_data = result.stdout
            healthy_instances = status_data.count('"Status":"running"')
            
            metrics.append({
                "time": round(time.time() - start_time, 1),
                "healthy_instances": healthy_instances
            })
            
            time.sleep(10)  # Check every 10 seconds
        
        avg_health = sum(m["healthy_instances"] for m in metrics) / len(metrics) if metrics else 0
        
        return f"""📈 Monitoring Report for {app_name}:
Duration: {duration}s
Average healthy instances: {avg_health:.1f}
Total checks: {len(metrics)}
Status: {"✅ Stable" if avg_health > 0 else "⚠️ Issues detected"}"""
        
    except subprocess.CalledProcessError as e:
        return f"❌ Monitoring failed: {e.stderr}"

def cleanup_resources(app_name: str) -> str:
    """Clean up deployment resources"""
    import subprocess
    
    try:
        log_message(f"Cleaning up resources for {app_name}")
        
        # Stop app
        subprocess.run(['flyctl', 'apps', 'suspend', app_name], 
                      capture_output=True, check=True)
        
        # Remove Docker images (optional)
        try:
            subprocess.run(['docker', 'rmi', f"{app_name}:latest"], 
                          capture_output=True, check=True)
        except subprocess.CalledProcessError:
            pass  # Image might not exist
        
        return f"🧹 Cleaned up resources for {app_name}"
        
    except subprocess.CalledProcessError as e:
        return f"❌ Cleanup failed: {e.stderr}"

registry = {
    "log_message": log_message,
    "check_docker_status": check_docker_status,
    "build_docker_image": build_docker_image,
    "deploy_to_fly": deploy_to_fly,
    "scale_fly_app": scale_fly_app,
    "get_app_status": get_app_status,
    "create_dockerfile": create_dockerfile,
    "monitor_deployment": monitor_deployment,
    "cleanup_resources": cleanup_resources,
}