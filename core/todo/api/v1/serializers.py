from rest_framework import serializers
from ...models import Task
from django.contrib.auth.models import User



class TaskSerializer(serializers.ModelSerializer):
    relative_url = serializers.URLField(source='get_absolute_api_url', read_only=True)
    absolute_url = serializers.SerializerMethodField(method_name='get_abs_url')
    class Meta:
        model = Task
        fields = ["id", "user", "title", "complete", "relative_url", "absolute_url", "created_date"]
        read_only_fields = ["user"]
    
    def get_abs_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.pk)
    
    # a function to set how i want my jason to be shown
    def to_representation(self, instance):
        request = self.context.get('request')
        rep = super().to_representation(instance)
        # checks if we are in list page or in detail view page
        if request.parser_context.get('kwargs').get('pk'):
            # if it is detail page, it pops and deletes some data that there is no need to show them in detail page
            rep.pop('relative_url', None)
            rep.pop('absolute_url', None)
        return rep
    
    # override the default create method
    def create(self, validated_data):
        validated_data['user'] = User.objects.get(id = self.context.get('request').user.id)
        return super().create(validated_data)
