# Generated by Django 4.1.7 on 2023-05-29 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_app', '0023_modelalert_deleted_modeldatasource_deleted_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='modeldatasource',
            name='lastUpdate',
            field=models.CharField(default='None', max_length=250),
        ),
    ]