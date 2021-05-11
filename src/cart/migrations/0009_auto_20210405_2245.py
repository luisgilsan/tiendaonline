# Generated by Django 3.1 on 2021-04-06 03:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0008_auto_20210405_2244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='primary_category_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='primary_products', to='cart.category'),
        ),
    ]