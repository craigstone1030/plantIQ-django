# Generated by Django 4.1.7 on 2023-05-27 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_app', '0021_alter_modelalerthistory_alertat'),
    ]

    operations = [
        migrations.AddField(
            model_name='modeldetector',
            name='lastScore',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='modeldetector',
            name='maxAnomaly',
            field=models.FloatField(default=0),
        ),
    ]
