# Paste this content into the file that
#   python manage.py makemigrations portfolio --empty -n unique_email_index
# generates for you (it will already have the correct `dependencies` line
# for whatever migration state your project is actually in — don't copy
# the dependencies line below, keep the one it generates).

from django.db import migrations


def add_unique_email_index(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == 'sqlite':
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS portfolio_uniq_user_email_ci "
                "ON auth_user (email COLLATE NOCASE)"
            )
        elif vendor == 'postgresql':
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS portfolio_uniq_user_email_ci "
                "ON auth_user (LOWER(email))"
            )
        elif vendor == 'mysql':
            cursor.execute(
                "ALTER TABLE auth_user ADD UNIQUE INDEX portfolio_uniq_user_email_ci "
                "((LOWER(email)))"
            )
        # Any other backend: skip — RegisterForm/ProfileEditForm's
        # application-level check still enforces uniqueness either way.


def remove_unique_email_index(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == 'mysql':
            cursor.execute("ALTER TABLE auth_user DROP INDEX portfolio_uniq_user_email_ci")
        else:
            cursor.execute("DROP INDEX IF EXISTS portfolio_uniq_user_email_ci")


class Migration(migrations.Migration):

    dependencies = [
        # keep whatever makemigrations --empty put here
    ]

    operations = [
        migrations.RunPython(add_unique_email_index, remove_unique_email_index),
    ]
