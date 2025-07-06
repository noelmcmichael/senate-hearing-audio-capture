#!/usr/bin/env python3
"""
Deploy UI improvements to production
"""

import subprocess
import sys
import os
import time

def run_command(cmd, description):
    """Run shell command with error handling"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def deploy_ui_improvements():
    """Deploy the UI improvements to production"""
    
    print("🚀 Deploying UI Improvements to Production")
    print("=" * 50)
    
    # Change to project directory
    project_dir = "/Users/noelmcmichael/Workspace/senate_hearing_audio_capture"
    os.chdir(project_dir)
    
    # Step 1: Ensure React build is up to date
    print("\n1. Building React Application")
    if not run_command("cd dashboard && npm run build", "React build"):
        return False
    
    # Step 2: Build Docker image
    print("\n2. Building Docker Image")
    image_tag = f"gcr.io/senate-hearing-capture/senate-hearing-processor:ui-improvements-{int(time.time())}"
    if not run_command(f"docker build -f Dockerfile.full -t {image_tag} .", "Docker build"):
        return False
    
    # Step 3: Push Docker image
    print("\n3. Pushing Docker Image to GCR")
    if not run_command(f"docker push {image_tag}", "Docker push"):
        return False
    
    # Step 4: Deploy to Cloud Run
    print("\n4. Deploying to Cloud Run")
    deploy_cmd = f"""
    gcloud run deploy senate-hearing-processor \
        --image={image_tag} \
        --region=us-central1 \
        --platform=managed \
        --allow-unauthenticated \
        --project=senate-hearing-capture \
        --memory=2Gi \
        --cpu=1 \
        --timeout=3600
    """
    if not run_command(deploy_cmd, "Cloud Run deployment"):
        return False
    
    print("\n🎉 Deployment Complete!")
    print("🔗 Check results at: https://senate-hearing-processor-518203250893.us-central1.run.app")
    
    # Step 5: Verify deployment
    print("\n5. Verifying Deployment")
    time.sleep(10)  # Wait for deployment to stabilize
    
    if run_command("curl -f https://senate-hearing-processor-518203250893.us-central1.run.app/health", "Health check"):
        print("✅ Deployment verification successful")
        return True
    else:
        print("⚠️  Deployment may need more time to become available")
        return False

if __name__ == "__main__":
    if not deploy_ui_improvements():
        print("\n❌ Deployment failed. Check the errors above and try again.")
        sys.exit(1)
    else:
        print("\n✅ Deployment successful! UI improvements are now live.")