# Generated by Django 3.1 on 2021-06-12 01:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0021_auto_20210612_0109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payupayment',
            name='name',
            field=models.CharField(blank=True, default=18, max_length=255, null=True),
        ),
    ]
