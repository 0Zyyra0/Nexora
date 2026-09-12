from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('work/', views.work_list, name='work_list'),
    path('work/<slug:slug>/', views.work_detail, name='work_detail'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
]
