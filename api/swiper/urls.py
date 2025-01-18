from django.urls import path
from .views import FirehoseView

urlpatterns = [
    path('posts/next/', FirehoseView.as_view(), name='next-post'),
    path('posts/swipe/', FirehoseView.as_view(), name='swipe-post'),
] 