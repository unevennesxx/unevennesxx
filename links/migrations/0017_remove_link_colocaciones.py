# Generated by Django 5.1 on 2024-08-15 14:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0016_alter_link_colocaciones'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='link',
            name='colocaciones',
        ),
    ]
