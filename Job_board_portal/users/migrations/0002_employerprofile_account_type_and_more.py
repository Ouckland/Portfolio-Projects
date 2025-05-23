# Generated by Django 5.2 on 2025-05-14 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employerprofile',
            name='account_type',
            field=models.CharField(choices=[('employer', 'Employer'), ('seeker', 'Job Seeker')], default=('employer', 'Employer'), max_length=10),
        ),
        migrations.AddField(
            model_name='seekerprofile',
            name='account_type',
            field=models.CharField(choices=[('employer', 'Employer'), ('seeker', 'Job Seeker')], default=('employer', 'Employer'), max_length=10),
        ),
        migrations.AlterField(
            model_name='seekerprofile',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
    ]
