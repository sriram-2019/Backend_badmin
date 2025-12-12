from rest_framework import serializers
from .models import Registration, Event, CompletedEvent, EventResult, EventResultImage
import base64

class RegistrationSerializer(serializers.ModelSerializer):
    # Don't include document in fields - handle it manually
    document = serializers.SerializerMethodField()

    class Meta:
        model = Registration
        fields = [
            'id',
            'name',
            'age',
            'dob',
            'gender',
            'state',
            'district',
            'level',
            'email',
            'phone_no',
            'address',
            'document',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_document(self, obj):
        """
        Convert binary data to base64 string for JSON response
        """
        if obj.document:
            try:
                # Convert binary to base64
                base64_data = base64.b64encode(obj.document).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_data}"
            except Exception as e:
                return None
        return None

    def create(self, validated_data):
        """
        Create registration with binary document data from file upload
        """
        # Get file from request.FILES
        request = self.context.get('request')
        document_binary = None
        
        if request and hasattr(request, 'FILES') and 'document' in request.FILES:
            file = request.FILES['document']
            document_binary = file.read()
            print(f"DEBUG Serializer: File read - Size: {len(document_binary)} bytes")
        
        # Create the registration
        registration = Registration.objects.create(**validated_data)
        
        # Set document binary data
        if document_binary:
            registration.document = document_binary
            registration.save(update_fields=['document'])
            print(f"DEBUG Serializer: Document saved - Size: {len(registration.document)} bytes")
        
        return registration

    def update(self, instance, validated_data):
        """
        Update registration with binary document data from file upload
        """
        # Get file from request.FILES
        request = self.context.get('request')
        document_binary = None
        
        if request and hasattr(request, 'FILES') and 'document' in request.FILES:
            file = request.FILES['document']
            document_binary = file.read()
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update document if provided
        if document_binary is not None:
            instance.document = document_binary
        
        instance.save()
        return instance

    def to_representation(self, instance):
        """
        Override to return base64 encoded image for reading
        """
        representation = super().to_representation(instance)
        
        # Convert binary to base64 for JSON response
        if instance.document:
            try:
                # Convert binary to base64
                base64_data = base64.b64encode(instance.document).decode('utf-8')
                representation['document'] = f"data:image/jpeg;base64,{base64_data}"
                representation['document_exists'] = True
                representation['document_name'] = f"document_{instance.id}.jpg"
            except Exception as e:
                representation['document'] = None
                representation['document_exists'] = False
                representation['document_name'] = None
        else:
            representation['document'] = None
            representation['document_exists'] = False
            representation['document_name'] = None
            
        return representation



class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id',
            'event_name',
            'registration_from',
            'registration_to',
            'registration_deadline_time',
            'event_from',
            'event_to',
            'event_time',
            'event_place',
            'age_limit',
            'categories',
            'entry_fee',
            'winner_prize',
            'runner_prize',
            'semifinalist_prize',
            'other_awards',
            'rules',
            'category_times',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CompletedEventSerializer(serializers.ModelSerializer):
    """
    Serializer for CompletedEvent model.
    Handles binary poster data similar to EventSerializer.
    """
    poster = serializers.SerializerMethodField()
    
    class Meta:
        model = CompletedEvent
        fields = [
            'id',
            'event_name',
            'event_conducted_date',
            'poster',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_poster(self, obj):
        """
        Convert binary data to base64 string for JSON response
        """
        if obj.poster:
            try:
                base64_data = base64.b64encode(obj.poster).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_data}"
            except Exception as e:
                return None
        return None
    
    def create(self, validated_data):
        """
        Create completed event with binary poster data from file upload
        """
        request = self.context.get('request')
        poster_binary = None
        
        if request and hasattr(request, 'FILES') and 'poster' in request.FILES:
            file = request.FILES['poster']
            poster_binary = file.read()
        
        completed_event = CompletedEvent.objects.create(**validated_data)
        
        if poster_binary:
            completed_event.poster = poster_binary
            completed_event.save(update_fields=['poster'])
        
        return completed_event
    
    def update(self, instance, validated_data):
        """
        Update completed event with binary poster data from file upload
        """
        request = self.context.get('request')
        poster_binary = None
        
        if request and hasattr(request, 'FILES') and 'poster' in request.FILES:
            file = request.FILES['poster']
            poster_binary = file.read()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if poster_binary is not None:
            instance.poster = poster_binary
        
        instance.save()
        return instance


class EventResultImageSerializer(serializers.ModelSerializer):
    """
    Serializer for EventResultImage model.
    Handles binary image data.
    """
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = EventResultImage
        fields = ['id', 'image', 'image_order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image(self, obj):
        """
        Convert binary data to base64 string for JSON response
        """
        if obj.image:
            try:
                base64_data = base64.b64encode(obj.image).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_data}"
            except Exception as e:
                return None
        return None


class EventResultSerializer(serializers.ModelSerializer):
    """
    Serializer for EventResult model.
    Includes nested images.
    """
    images = EventResultImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = EventResult
        fields = [
            'id',
            'event_name',
            'event_date',
            'winner',
            'images',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """
        Create event result with multiple images from file uploads
        """
        request = self.context.get('request')
        event_result = EventResult.objects.create(**validated_data)
        
        if request and hasattr(request, 'FILES'):
            image_files = []
            for key in request.FILES.keys():
                if key.startswith('image_'):
                    image_files.append((int(key.split('_')[1]), request.FILES[key]))
            
            image_files.sort(key=lambda x: x[0])
            
            for index, file in image_files:
                image_binary = file.read()
                EventResultImage.objects.create(
                    event_result=event_result,
                    image=image_binary,
                    image_order=index
                )
        
        return event_result

