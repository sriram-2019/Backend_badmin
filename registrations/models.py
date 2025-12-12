from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class Registration(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    LEVEL_CHOICES = [
        ('National', 'National'),
        ('State', 'State'),
        ('District', 'District'),
    ]

    name = models.CharField(max_length=200)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    dob = models.DateField(null=True, blank=True)              # 👈 NEW
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    state = models.CharField(max_length=100, blank=True)       # 👈 NEW
    district = models.CharField(max_length=100, blank=True)    # 👈 NEW
    level = models.CharField(                                 # 👈 NEW
        max_length=20, choices=LEVEL_CHOICES, blank=True
    )

    email = models.EmailField(blank=True)                      # 👈 NEW
    phone_no = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)                     # 👈 NEW

    # Store image as binary BLOB in database
    document = models.BinaryField(null=True, blank=True, editable=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}"


class AdminAccount(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)  # stores hashed password

    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username
class Event(models.Model):
    event_name = models.CharField(max_length=200)
    registration_from = models.DateField()
    registration_to = models.DateField()
    registration_deadline_time = models.TimeField(null=True, blank=True, help_text="Registration deadline time (e.g., 8:00 PM)")
    event_from = models.DateField()
    event_to = models.DateField(null=True, blank=True)  
    event_time = models.TimeField(null=True, blank=True, help_text="Event start time (e.g., 9:00 AM)")
    event_place = models.CharField(max_length=255)
    age_limit = models.CharField(max_length=100, blank=True, help_text="Global age limit (optional - age limits are now part of categories)")  # e.g., "below 18", "above 18", "18+", etc.
    
    # Tournament-specific fields
    categories = models.TextField(blank=True, help_text="Tournament categories with start times. Format: 'Category Name Age Limit: HH:MM' (e.g., 'Women's Doubles Below 30: 12:00'). One per line or comma-separated.")
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Entry fee amount")
    winner_prize = models.CharField(max_length=200, blank=True, help_text="Winner prize (e.g., '2500+Trophy')")
    runner_prize = models.CharField(max_length=200, blank=True, help_text="Runner-up prize (e.g., '1500+Trophy')")
    semifinalist_prize = models.CharField(max_length=200, blank=True, help_text="Semifinalist prize (e.g., 'Trophy')")
    other_awards = models.TextField(blank=True, help_text="Other awards or gifts (e.g., 'BEST PLAYER AWARDS & OTHER SURPRISING GIFTS')")
    rules = models.TextField(blank=True, help_text="Tournament rules. One rule per line.")
    category_times = models.TextField(blank=True, help_text="[Legacy field] Category start times. Categories now include times in the categories field. This field is kept for backward compatibility.")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Most recent first

    def __str__(self):
        return self.event_name
    
    def is_ended(self):
        """Check if the event has ended based on event_to or event_from"""
        from django.utils import timezone
        today = timezone.now().date()
        # If event_to exists, check if it's in the past
        if self.event_to:
            return self.event_to < today
        # Otherwise, check if event_from is in the past
        return self.event_to is None and self.event_from < today
    
    def is_upcoming(self):
        """Check if the event is upcoming (not ended)"""
        return not self.is_ended()


class CompletedEvent(models.Model):
    """
    Separate model for completed events (past events that have been conducted).
    This is simpler than Event model - only stores name, date, and poster.
    """
    event_name = models.CharField(max_length=200)
    event_conducted_date = models.DateField(help_text="Date when the event was conducted")
    
    # Poster image stored as binary data
    poster = models.BinaryField(null=True, blank=True, editable=True, help_text="Event poster image stored as binary (JPG/JPEG/PNG)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_conducted_date']  # Most recent first by event date
        verbose_name = "Completed Event"
        verbose_name_plural = "Completed Events"
    
    def __str__(self):
        return f"{self.event_name} ({self.event_conducted_date})"


class EventResult(models.Model):
    """
    Model for storing event results after completion.
    Stores event name, date, winner, and multiple event images.
    """
    event_name = models.CharField(max_length=200, help_text="Name of the completed event")
    event_date = models.DateField(help_text="Date when the event was conducted")
    winner = models.CharField(max_length=500, blank=True, help_text="Winner(s) of the event")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-event_date']  # Most recent first
        verbose_name = "Event Result"
        verbose_name_plural = "Event Results"
    
    def __str__(self):
        return f"{self.event_name} - {self.event_date}"


class EventResultImage(models.Model):
    """
    Model for storing multiple images for an event result.
    Each image is stored as binary data.
    """
    event_result = models.ForeignKey(EventResult, on_delete=models.CASCADE, related_name='images')
    image = models.BinaryField(help_text="Event image stored as binary (JPG/JPEG/PNG)")
    image_order = models.PositiveIntegerField(default=0, help_text="Order of image display")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['image_order', 'created_at']
        verbose_name = "Event Result Image"
        verbose_name_plural = "Event Result Images"
    
    def __str__(self):
        return f"Image {self.image_order} for {self.event_result.event_name}"
