# Run this once via python manage.py shell
# or put it in a data migration

from django.contrib.auth.models import Group, Permission

# Create the 'Blog Admin' group
admin_group, created = Group.objects.get_or_create(name='Blog Admin')

# Give them specific permissions
permissions = Permission.objects.filter(codename__in=[
    'change_user',        # can edit users
    'view_user',          # can view users
    'change_blog',        # can edit blogs
    'view_blog',          # can view blogs
    'delete_comment',     # can delete comments
    'view_comment',       # can view comments
    'change_topic',       # can edit topics
    'view_topic',         # can view topics
])

admin_group.permissions.set(permissions)

# What they CANNOT do (not in the list above):
# delete_user   ← cannot delete users, only deactivate via API
# add_user      ← cannot create users from admin panel
# delete_blog   ← cannot hard delete blogs