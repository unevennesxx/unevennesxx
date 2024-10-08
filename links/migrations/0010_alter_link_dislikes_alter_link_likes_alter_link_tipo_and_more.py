# Generated by Django 5.1 on 2024-08-15 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0009_alter_link_dislikes_alter_link_likes_alter_link_tipo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='link',
            name='dislikes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='link',
            name='likes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='link',
            name='tipo',
            field=models.CharField(choices=[('Samplicious', 'Samplicious'), ('Spectrum', 'Spectrum'), ('Cint', 'Cint'), ('Progede', 'Progede'), ('Sample-cube', 'Sample-cube'), ('Invite', 'Invite'), ('Internos', 'Internos')], default='Samplicious', max_length=50),
        ),
        migrations.AlterField(
            model_name='link',
            name='url',
            field=models.URLField(max_length=500),
        ),
    ]
