# Generated by Django 3.1 on 2021-03-21 03:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0004_auto_20210320_2217'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='available_colour',
            new_name='available_colours',
        ),
    ]