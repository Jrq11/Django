# Generated by Django 5.1.7 on 2025-03-23 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_alter_room_availability'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='availability',
            field=models.CharField(choices=[('Occupied', 'Occupied'), ('Vacant', 'Vacant'), ('Under Renuevation', 'Under Renuevation')], default='Vacant', max_length=17),
        ),
    ]
