from django.urls import path

from channels import views

app_name = "channels"

urlpatterns = [
    path("", views.channel_home, name="home"),
    path("facebook/connect/", views.facebook_connect, name="facebook_connect"),
    path("facebook/callback/", views.facebook_callback, name="facebook_callback"),
    path("facebook/pages/", views.my_pages_json, name="facebook_pages"),
    path("facebook/page-posts/", views.page_posts_json, name="page_posts"),
]
