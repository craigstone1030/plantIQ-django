# Generated by Django 4.1.7 on 2023-05-06 04:20

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base_app', '0014_alter_modelalert_duration_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='modelalert',
            name='duration',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='modelalerthistory',
            name='alertAt',
            field=models.DateTimeField(default=datetime.datetime(2023, 5, 6, 4, 20, 44, 433122)),
        ),
    ]
