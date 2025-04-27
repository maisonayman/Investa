import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import upload_project_picture
from firebase_admin import db

@csrf_exempt
def create_project(request):
    if request.method == 'POST':
        try:
            # 1. Handle project picture upload
            project_picture_url = None
            if "project_picture" in request.FILES:
                project_picture = request.FILES["project_picture"]
                project_picture_url = upload_project_picture(project_picture, project_picture.name)

            # 2. Parse other project data
            project_data = request.POST
            project_info = {
                "project_name": project_data.get("project_name"),
                "description": project_data.get("description"),
                "category": project_data.get("category"),

            }

            if project_picture_url:
                project_info["project_picture_url"] = project_picture_url

            # 3. Save to Firebase
            projects_ref = db.reference("projects")
            projects_ref.push(project_info)

            return JsonResponse({"status": "success", "data": project_info}, status=201)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "fail", "message": "Only POST allowed"}, status=405)

