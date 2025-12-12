from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.utils import timezone
from django.db import models as db_models
import os
import csv
import json

from rest_framework import viewsets, status, renderers
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Registration, AdminAccount, Event, CompletedEvent, EventResult, EventResultImage
from .serializers import RegistrationSerializer, LoginSerializer, EventSerializer, CompletedEventSerializer, EventResultSerializer

# Minimal CSV renderer to satisfy content negotiation for CSV endpoint
class PassthroughCSVRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class RegistrationViewSet(viewsets.ModelViewSet):
    """
    CRUD for registrations. Allows multipart/form-data for file uploads.
    """
    queryset = Registration.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]            # adjust for production
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        """
        Add request to serializer context so document URLs can be built.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        """
        Filter registrations based on event date ranges.
        Query params:
        - ?event_id=X: Filter by specific event's date ranges (registration_from to event_to)
        """
        queryset = super().get_queryset()
        
        # Filter by event_id - get registrations within that event's date ranges
        event_id = self.request.query_params.get('event_id')
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                # Get registrations created between registration_from and event_to (or event_from if no event_to)
                start_date = event.registration_from
                end_date = event.event_to if event.event_to else event.event_from
                
                # Convert dates to datetime for comparison with created_at
                from datetime import datetime, time as dt_time
                
                start_datetime = timezone.make_aware(datetime.combine(start_date, dt_time.min))
                end_datetime = timezone.make_aware(datetime.combine(end_date, dt_time.max))
                
                queryset = queryset.filter(
                    created_at__gte=start_datetime,
                    created_at__lte=end_datetime
                )
            except Event.DoesNotExist:
                pass
        
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Override create to debug file upload issues.
        """
        # Debug: Check if file is in request
        if 'document' in request.FILES:
            file = request.FILES['document']
            print(f"DEBUG: File received - Name: {file.name}, Size: {file.size}, Content-Type: {file.content_type}")
        else:
            print("DEBUG: No 'document' file in request.FILES")
            print(f"DEBUG: Available files: {list(request.FILES.keys())}")
        
        # Debug: Check all form data
        print(f"DEBUG: Form data keys: {list(request.data.keys())}")
        
        return super().create(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Response: { "token": "<signed-string>" }
    """
    authentication_classes = []   # disable session auth for login
    permission_classes = [AllowAny]  # allow anyone to POST

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            admin = AdminAccount.objects.get(username=username)
        except AdminAccount.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        if not admin.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        payload = {"admin_id": admin.id}
        token = signing.dumps(payload)  # signed string using SECRET_KEY

        return Response({"token": token})


class EventViewSet(viewsets.ModelViewSet):
    """
    CRUD for events. 
    GET /api/events/ - List all events (ordered by most recent first)
    GET /api/events/?upcoming=true - List only upcoming events (not ended)
    GET /api/events/?completed=true - List only completed/ended events
    POST /api/events/ - Create a new event
    GET /api/events/{id}/ - Get a specific event
    PUT /api/events/{id}/ - Update an event
    DELETE /api/events/{id}/ - Delete an event
    """
    queryset = Event.objects.all().order_by('-created_at')  # Most recent first
    serializer_class = EventSerializer
    permission_classes = [AllowAny]  # adjust for production if needed
    
    def get_queryset(self):
        """
        Filter events based on query parameters:
        - ?upcoming=true: Only return events that haven't ended
        - ?completed=true: Only return events that have ended
        - No filter: Return all events
        """
        queryset = super().get_queryset()
        
        upcoming = self.request.query_params.get('upcoming', '').lower() == 'true'
        completed = self.request.query_params.get('completed', '').lower() == 'true'
        
        if upcoming:
            # Return only upcoming events (not ended), ordered by most recently created first
            today = timezone.now().date()
            return queryset.filter(
                db_models.Q(event_to__gte=today) | 
                db_models.Q(event_to__isnull=True, event_from__gte=today)
            ).order_by('-created_at')  # Most recently created first
        
        if completed:
            # Return only completed/ended events
            today = timezone.now().date()
            return queryset.filter(
                db_models.Q(event_to__lt=today) |
                db_models.Q(event_to__isnull=True, event_from__lt=today)
            ).order_by('-event_from', '-event_to')
        
        # Default: return all events
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        Override list to ensure proper response format.
        Returns array of events.
        """
        response = super().list(request, *args, **kwargs)
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to return single event object.
        """
        response = super().retrieve(request, *args, **kwargs)
        return response


class CompletedEventViewSet(viewsets.ModelViewSet):
    """
    CRUD for completed events.
    GET /api/completed-events/ - List all completed events
    POST /api/completed-events/ - Create a new completed event
    GET /api/completed-events/{id}/ - Get a specific completed event
    PUT /api/completed-events/{id}/ - Update a completed event
    DELETE /api/completed-events/{id}/ - Delete a completed event
    """
    queryset = CompletedEvent.objects.all().order_by('-event_conducted_date')
    serializer_class = CompletedEventSerializer
    permission_classes = [AllowAny]  # adjust for production if needed
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_context(self):
        """
        Add request to serializer context so poster file can be accessed.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class EventResultViewSet(viewsets.ModelViewSet):
    """
    CRUD for event results.
    GET /api/event-results/ - List all event results
    POST /api/event-results/ - Create a new event result with multiple images
    GET /api/event-results/{id}/ - Get a specific event result
    PUT /api/event-results/{id}/ - Update an event result
    DELETE /api/event-results/{id}/ - Delete an event result
    """
    queryset = EventResult.objects.all().order_by('-event_date')
    serializer_class = EventResultSerializer
    permission_classes = [AllowAny]  # adjust for production if needed
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_context(self):
        """
        Add request to serializer context so image files can be accessed.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CheckDatabaseDataView(APIView):
    """
    GET /api/check-db-data/
    Returns raw database data to see how document field is stored.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        from django.db import connection
        import json
        from datetime import datetime
        
        registrations = Registration.objects.all()
        results = []
        
        for reg in registrations:
            # Get raw database value
            with connection.cursor() as cursor:
                cursor.execute("SELECT document FROM registrations_registration WHERE id = %s", [reg.id])
                row = cursor.fetchone()
                db_document_value = row[0] if row else None
            
            # Get all field values
            reg_data = {
                'id': reg.id,
                'name': reg.name,
                'age': reg.age,
                'dob': str(reg.dob) if reg.dob else None,
                'gender': reg.gender,
                'state': reg.state,
                'district': reg.district,
                'level': reg.level,
                'email': reg.email,
                'phone_no': reg.phone_no,
                'address': reg.address,
                'created_at': reg.created_at.isoformat() if reg.created_at else None,
                # Document field analysis
                'document_field_analysis': {
                    'has_document': bool(reg.document),
                    'document_size_bytes': len(bytes(reg.document)) if reg.document else None,
                    'database_raw_value_type': str(type(db_document_value)),
                    'database_value_is_binary': isinstance(db_document_value, (bytes, memoryview)) if db_document_value else False,
                }
            }
            results.append(reg_data)
        
        return Response({
            'message': 'Database inspection results',
            'total_registrations': len(results),
            'registrations': results,
            'note': 'Document is stored as binary BLOB directly in the database. No files are stored on disk.'
        })


class DownloadImageView(APIView):
    """
    GET /api/registrations/{id}/download-image/
    Downloads the image file to user's local machine from binary data in database.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk, *args, **kwargs):
        try:
            registration = Registration.objects.get(id=pk)
        except Registration.DoesNotExist:
            raise Http404("Registration not found")

        if not registration.document:
            return Response({
                "error": "No document found for this registration",
                "can_reupload": True
            }, status=status.HTTP_404_NOT_FOUND)

        try:
            # Get binary data from database
            binary_data = bytes(registration.document)
            
            # Create HTTP response with binary data
            response = HttpResponse(binary_data, content_type='image/jpeg')
            response['Content-Disposition'] = f'attachment; filename="document_{registration.id}.jpg"'
            return response
        except Exception as e:
            return Response({"error": f"Error reading document: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteImageFileView(APIView):
    """
    DELETE /api/registrations/{id}/delete-image-file/
    Soft-delete: for BinaryField storage, keep the binary so users can
    still view/download again. Just return a success message without
    removing data. This lets users repeat view/download/delete cycles.
    """
    permission_classes = [AllowAny]

    def delete(self, request, pk, *args, **kwargs):
        try:
            registration = Registration.objects.get(id=pk)
        except Registration.DoesNotExist:
            return Response({"error": "Registration not found"}, status=status.HTTP_404_NOT_FOUND)

        if not registration.document:
            return Response({"error": "No document found for this registration"}, status=status.HTTP_404_NOT_FOUND)

        # Soft-delete: do not actually remove binary data so it can be viewed/downloaded again
        document_size = len(bytes(registration.document)) if registration.document else 0

        return Response({
            "message": "Delete acknowledged (soft delete). Document is kept so you can view/download again.",
            "document_preserved": True,
            "size_bytes": document_size,
            "note": "Binary document not removed; repeat view/download/delete is allowed."
        })


class DownloadRegistrationsDataView(APIView):
    """
    GET /api/download-registrations/
    Downloads all registration data as CSV or JSON.
    Query param: ?format=csv or ?format=json (default: json)
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        format_type = request.query_params.get('format', 'json').lower()
        registrations = Registration.objects.all().order_by('-created_at')
        
        if format_type == 'csv':
            # Generate CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="registrations.csv"'
            
            writer = csv.writer(response)
            # Write header (without Document column)
            writer.writerow([
                'ID', 'Name', 'Age', 'Date of Birth', 'Gender', 'State', 'District',
                'Level', 'Email', 'Phone Number', 'Address', 'Created At'
            ])
            
            # Write data (without Document column)
            for reg in registrations:
                writer.writerow([
                    reg.id,
                    reg.name or '',
                    reg.age or '',
                    reg.dob.strftime('%Y-%m-%d') if reg.dob else '',
                    reg.gender or '',
                    reg.state or '',
                    reg.district or '',
                    reg.level or '',
                    reg.email or '',
                    reg.phone_no or '',
                    reg.address or '',
                    reg.created_at.strftime('%Y-%m-%d %H:%M:%S') if reg.created_at else '',
                ])
            
            return response
        
        else:
            # Generate JSON
            data = []
            for reg in registrations:
                data.append({
                    'id': reg.id,
                    'name': reg.name,
                    'age': reg.age,
                    'dob': str(reg.dob) if reg.dob else None,
                    'gender': reg.gender,
                    'state': reg.state,
                    'district': reg.district,
                    'level': reg.level,
                    'email': reg.email,
                    'phone_no': reg.phone_no,
                    'address': reg.address,
                    'document': 'Yes' if reg.document else None,
                    'document_size_bytes': len(bytes(reg.document)) if reg.document else None,
                    'created_at': reg.created_at.isoformat() if reg.created_at else None,
                })
            
            response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="registrations.json"'
            return response


class CleanupEndedEventsView(APIView):
    """
    DELETE /api/events/cleanup-ended/
    Delete all events that have ended (event_to < today or event_from < today if no event_to).
    Optionally delete associated registrations if delete_registrations=true.
    """
    permission_classes = [AllowAny]

    def delete(self, request, *args, **kwargs):
        today = timezone.now().date()
        
        # Find ended events
        ended_events = Event.objects.filter(
            db_models.Q(event_to__lt=today) |
            db_models.Q(event_to__isnull=True, event_from__lt=today)
        )
        
        event_count = ended_events.count()
        event_ids = list(ended_events.values_list('id', flat=True))
        
        # Check if user wants to delete registrations too
        delete_registrations = request.query_params.get('delete_registrations', 'false').lower() == 'true'
        
        if delete_registrations:
            # Delete registrations associated with these events (if you have event-registration relationship)
            # For now, we'll just delete the events
            # If you have a foreign key relationship, uncomment this:
            # Registration.objects.filter(event_id__in=event_ids).delete()
            pass
        
        # Delete the ended events
        ended_events.delete()
        
        return Response({
            'message': f'Successfully deleted {event_count} ended event(s)',
            'deleted_event_ids': event_ids,
            'delete_registrations': delete_registrations,
            'note': 'Events that have ended (event_to < today) have been removed from the database.'
        })


class CheckEventDataView(APIView):
    """
    GET /api/events/check-data/
    Debug endpoint to check what data is stored in the database for events.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        import re
        events = Event.objects.all().order_by('-created_at')
        results = []
        
        for event in events:
            # Parse categories
            categories_list = []
            if event.categories:
                categories_list = [c.strip() for c in re.split(r'[,\n]', event.categories) if c.strip()]
            
            # Parse category times
            category_times_list = []
            if event.category_times:
                category_times_list = [t.strip() for t in re.split(r'[,\n]', event.category_times) if t.strip()]
            
            event_data = {
                'id': event.id,
                'event_name': event.event_name,
                'categories_raw': event.categories,
                'categories_parsed': categories_list,
                'category_times_raw': event.category_times,
                'category_times_parsed': category_times_list,
                'entry_fee': str(event.entry_fee) if event.entry_fee else None,
                'winner_prize': event.winner_prize,
                'runner_prize': event.runner_prize,
                'semifinalist_prize': event.semifinalist_prize,
                'other_awards': event.other_awards,
                'rules': event.rules,
                'registration_from': str(event.registration_from),
                'registration_to': str(event.registration_to),
                'registration_deadline_time': str(event.registration_deadline_time) if event.registration_deadline_time else None,
                'event_from': str(event.event_from),
                'event_to': str(event.event_to) if event.event_to else None,
                'event_time': str(event.event_time) if event.event_time else None,
                'event_place': event.event_place,
                'age_limit': event.age_limit,
                'created_at': event.created_at.isoformat() if event.created_at else None,
            }
            results.append(event_data)
        
        return Response({
            'message': 'Event data inspection',
            'total_events': len(results),
            'events': results,
            'note': 'This shows raw database values for debugging. Check categories_raw and category_times_raw to see what is stored.'
        })


class ExportRegistrationsCsvView(APIView):
    """
    GET /api/registrations/export/csv/
    GET /api/registrations/export/csv/?event_id=X
    Dedicated CSV export endpoint. Can filter by event_id.
    """
    permission_classes = [AllowAny]
    renderer_classes = [PassthroughCSVRenderer]

    def get(self, request, *args, **kwargs):
        # Get base queryset
        registrations = Registration.objects.all()
        
        # Filter by event_id if provided
        event_id = request.query_params.get('event_id')
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                # Get registrations created between registration_from and event_to (or event_from if no event_to)
                start_date = event.registration_from
                end_date = event.event_to if event.event_to else event.event_from
                
                # Convert dates to datetime for comparison with created_at
                from datetime import datetime, time as dt_time
                
                start_datetime = timezone.make_aware(datetime.combine(start_date, dt_time.min))
                end_datetime = timezone.make_aware(datetime.combine(end_date, dt_time.max))
                
                registrations = registrations.filter(
                    created_at__gte=start_datetime,
                    created_at__lte=end_datetime
                )
            except Event.DoesNotExist:
                pass
        
        registrations = registrations.order_by('-created_at')
        response = HttpResponse(content_type='text/csv')
        
        # Generate filename based on event filter
        if event_id:
            try:
                event = Event.objects.get(id=event_id)
                filename = f"registrations_{event.event_name.replace(' ', '_')}_{event_id}.csv"
            except Event.DoesNotExist:
                filename = "registrations.csv"
        else:
            filename = "registrations.csv"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Age', 'Date of Birth', 'Gender', 'State', 'District',
            'Level', 'Email', 'Phone Number', 'Address', 'Document', 'Created At'
        ])

        for reg in registrations:
            writer.writerow([
                reg.id,
                reg.name or '',
                reg.age or '',
                reg.dob.strftime('%Y-%m-%d') if reg.dob else '',
                reg.gender or '',
                reg.state or '',
                reg.district or '',
                reg.level or '',
                reg.email or '',
                reg.phone_no or '',
                reg.address or '',
                'Yes' if reg.document else 'No',
                reg.created_at.strftime('%Y-%m-%d %H:%M:%S') if reg.created_at else '',
            ])

        return response
