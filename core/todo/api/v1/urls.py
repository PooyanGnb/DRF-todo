from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter, SimpleRouter


app_name = 'api-v1'

router = DefaultRouter()
router.register('task',views.TaskModelViewSet, basename='task')
urlpatterns = router.urls