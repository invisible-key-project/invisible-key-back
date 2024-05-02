import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
def receive_and_process_qrdata(request):
    data = json.loads(request.body)
    qr_id = data.get('id')
    qr_date = data.get('date')

    # id + date
    data = f"{qr_id}{qr_date}"


    return JsonResponse({'status': 'success', 'message': data})
