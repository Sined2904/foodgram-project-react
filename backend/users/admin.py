from django.contrib import admin


from .models import User, Follow


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
    )
    search_fields = ('username',)
    list_filter = ('username', 'email')
    empty_value_display = '-пусто-'
    ordering = ['username']

class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    empty_value_display = '-пусто-'
    ordering = ['user']

admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)