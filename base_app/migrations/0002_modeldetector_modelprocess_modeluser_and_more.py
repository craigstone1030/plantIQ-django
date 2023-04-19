# Generated by Django 4.1.7 on 2023-04-17 14:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("base_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelDetector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=250)),
                ("description", models.CharField(max_length=250)),
                ("processId", models.IntegerField(default=-1)),
                ("metricsList", models.TextField(max_length=4096)),
            ],
            options={
                "db_table": "tbl_detector",
            },
        ),
        migrations.CreateModel(
            name="ModelProcess",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=250)),
                ("description", models.CharField(max_length=250)),
                ("datasourceId", models.IntegerField(default=-1)),
                ("metricsList", models.TextField(max_length=4096)),
            ],
            options={
                "db_table": "tbl_process",
            },
        ),
        migrations.CreateModel(
            name="ModelUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("firName", models.CharField(max_length=250)),
                ("lastName", models.CharField(max_length=250)),
                ("email", models.CharField(max_length=250)),
                ("mobileNumber", models.CharField(max_length=250)),
                ("company", models.CharField(max_length=250)),
            ],
            options={
                "db_table": "tbl_user",
            },
        ),
        migrations.AddField(
            model_name="modeldatasource",
            name="userId",
            field=models.IntegerField(default=-1),
        ),
    ]
