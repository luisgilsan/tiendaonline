# Generated by Django 3.1 on 2021-03-21 03:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0003_auto_20210320_2057'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColourVariation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='orderitem',
            name='colour',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cart.colourvariation'),
        ),
        migrations.AddField(
            model_name='product',
            name='available_colour',
            field=models.ManyToManyField(to='cart.ColourVariation'),
        ),
    ]