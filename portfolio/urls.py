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
    path('blog/<slug:slug>/comment/', views.comment_create, name='comment_create'),
    path('blog/<slug:slug>/like/', views.like_toggle, name='like_toggle'),
    path('blog/<slug:slug>/save/', views.bookmark_toggle, name='bookmark_toggle'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.profile_dashboard, name='profile_dashboard'),
    path('accounts/profile/edit/', views.profile_edit, name='profile_edit'),
    path('accounts/profile/password/', views.profile_password_change, name='profile_password_change'),
    path('accounts/profile/security/', views.profile_security_edit, name='profile_security_edit'),
    path('accounts/recover/', views.recover_step1, name='recover_step1'),
    path('accounts/recover/question/', views.recover_step2, name='recover_step2'),
    path('accounts/recover/reset/', views.recover_step3, name='recover_step3'),
]
