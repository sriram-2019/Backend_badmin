from django.contrib import admin
from django.utils.html import format_html

from .models import Registration, Event


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):

    # Columns visible in the admin list view
    list_display = (
        'id',
        'name',
        'age',
        'dob',
        'gender',
        'phone_no',
        'email',
        'level',
        'state',
        'district',
        'created_at',
        'document_link',
    )

    # Searchable fields
    search_fields = (
        'name',
        'phone_no',
        'email',
        'state',
        'district',
    )

    # Sidebar filters
    list_filter = (
        'gender',
        'level',
        'state',
        'district',
    )

    # Make created_at read-only in the admin form (optional but usually correct)
    readonly_fields = ('created_at',)

    # Clickable PDF/JPG link in admin
    def document_link(self, obj):
        if obj.document:
            # Styled like a small button
            return format_html(
                '<a href="{}" target="_blank" '
                'style="padding: 3px 8px; border-radius: 4px; '
                'background: #417690; color: white; text-decoration: none;">'
                'View</a>',
                obj.document.url,
            )
        return '-'

    document_link.short_description = 'Document'
    document_link.admin_order_field = 'document'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    # Columns visible in the admin list view
    list_display = (
        'id',
        'event_name',
        'event_place',
        'event_from',
        'event_to',
        'registration_from',
        'registration_to',
        'age_limit',
        'created_at',
    )
    
    # Searchable fields
    search_fields = (
        'event_name',
        'event_place',
    )
    
    # Sidebar filters
    list_filter = (
        'event_from',
        'event_to',
        'age_limit',
        'created_at',
    )
    
    # Make created_at read-only in the admin form
    readonly_fields = ('created_at',)
    
    # Date hierarchy for easy navigation
    date_hierarchy = 'created_at'
