from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegistrationViewSet, LoginView, EventViewSet, CompletedEventViewSet,
    EventResultViewSet, CheckDatabaseDataView, DownloadImageView, DeleteImageFileView,
    DownloadRegistrationsDataView, ExportRegistrationsCsvView, CheckEventDataView
)

router = DefaultRouter()
router.register(r'registrations', RegistrationViewSet, basename='registrations')
router.register(r'events', EventViewSet, basename='events')
router.register(r'completed-events', CompletedEventViewSet, basename='completed-events')
router.register(r'event-results', EventResultViewSet, basename='event-results')

urlpatterns = [
    # Router URLs
    path("", include(router.urls)),
    
    # POST /api/auth/login/  -> LoginView
    path("auth/login/", LoginView.as_view(), name="api_login"),
    # GET /api/check-db-data/ -> CheckDatabaseDataView (for debugging)
    path("check-db-data/", CheckDatabaseDataView.as_view(), name="check_db_data"),
    # GET /api/events/check-data/ -> CheckEventDataView (for debugging event data)
    path("events/check-data/", CheckEventDataView.as_view(), name="check_event_data"),
    # GET /api/registrations/{id}/download-image/ -> DownloadImageView
    path("registrations/<int:pk>/download-image/", DownloadImageView.as_view(), name="download_image"),
    # DELETE /api/registrations/{id}/delete-image-file/ -> DeleteImageFileView
    path("registrations/<int:pk>/delete-image-file/", DeleteImageFileView.as_view(), name="delete_image_file"),
    # GET /api/download-registrations/?format=csv or ?format=json -> DownloadRegistrationsDataView
    path("download-registrations/", DownloadRegistrationsDataView.as_view(), name="download_registrations"),
    # GET /api/registrations/export/csv/ -> ExportRegistrationsCsvView (CSV only)
    path("registrations/export/csv/", ExportRegistrationsCsvView.as_view(), name="export_registrations_csv"),
]
